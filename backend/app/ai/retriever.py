"""Utilities for vector search and retrieval that combine internal data with live SERP intelligence."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List, Optional, Sequence

import structlog
from langchain.embeddings.base import Embeddings
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.vectorstores import Qdrant as QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

logger = structlog.get_logger(__name__)


@dataclass
class VectorStoreConfig:
    """Configuration for vector store collections."""

    collection_name: str
    distance: qmodels.Distance = qmodels.Distance.COSINE
    vector_size: Optional[int] = None
    metadata_schema: Optional[qmodels.PayloadSchema] = None


class QdrantVectorStoreManager:
    """Manage Qdrant collections and expose LangChain compatible helpers."""

    def __init__(
        self,
        client: QdrantClient,
        embeddings: Embeddings,
        config: VectorStoreConfig,
    ) -> None:
        self.client = client
        self.embeddings = embeddings
        self.config = config
        self._vectorstore: Optional[QdrantVectorStore] = None

    def ensure_collection(self, vector_size: Optional[int] = None) -> None:
        """Create the collection in Qdrant if it does not exist."""

        size = vector_size or self.config.vector_size
        if size is None:
            raise ValueError("Vector size must be provided on first initialisation")

        existing = [c.name for c in self.client.get_collections().collections]
        if self.config.collection_name in existing:
            logger.debug(
                "qdrant.collection.exists",
                collection=self.config.collection_name,
            )
            return

        logger.info(
            "qdrant.collection.create",
            collection=self.config.collection_name,
            vector_size=size,
        )
        vectors_config = qmodels.VectorParams(size=size, distance=self.config.distance)
        self.client.create_collection(
            collection_name=self.config.collection_name,
            vectors_config=vectors_config,
            payload_schema=self.config.metadata_schema,
        )

    @property
    def vectorstore(self) -> QdrantVectorStore:
        """Return a lazily constructed LangChain vector store."""

        if self._vectorstore is None:
            self._vectorstore = QdrantVectorStore(
                client=self.client,
                collection_name=self.config.collection_name,
                embeddings=self.embeddings,
            )
        return self._vectorstore

    def upsert_documents(self, documents: Sequence[Document]) -> None:
        """Add or update documents in Qdrant."""

        if not documents:
            return

        logger.info(
            "qdrant.upsert",
            collection=self.config.collection_name,
            count=len(documents),
        )
        self.vectorstore.add_documents(list(documents))

    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Perform a similarity search against the managed collection."""

        return self.vectorstore.similarity_search(query, k=k)


class SERPService:
    """Fetch SERP data for enrichment. Real implementations can call external APIs."""

    def __init__(self, http_client, prompt: Optional[PromptTemplate] = None) -> None:
        self.http_client = http_client
        self.prompt = prompt

    async def fetch_results(self, query: str, top_k: int = 5) -> List[Document]:
        """Return SERP snippets as Documents. Placeholder uses prompt when API unavailable."""

        # This placeholder fabricates SERP summaries using the LLM prompt.
        if self.prompt is None:
            return []
        logger.info("serp.fetch", query=query, top_k=top_k)
        text = self.prompt.format(query=query)
        return [
            Document(
                page_content=text,
                metadata={
                    "source": "serp",
                    "query": query,
                    "rank": 1,
                },
            )
        ]


class CombinedRetriever:
    """Aggregate multiple retrievers (internal, competitor, SERP) into a single interface."""

    def __init__(
        self,
        internal_store: Optional[QdrantVectorStoreManager] = None,
        competitor_store: Optional[QdrantVectorStoreManager] = None,
        serp_service: Optional[SERPService] = None,
    ) -> None:
        self.internal_store = internal_store
        self.competitor_store = competitor_store
        self.serp_service = serp_service

    async def aget_relevant_documents(self, query: str, k: int = 5) -> List[Document]:
        """Async entry point used by LangChain for retrieval augmented generation."""

        tasks = []
        if self.internal_store is not None:
            tasks.append(
                asyncio.get_running_loop().run_in_executor(
                    None, self.internal_store.similarity_search, query, k
                )
            )
        if self.competitor_store is not None:
            tasks.append(
                asyncio.get_running_loop().run_in_executor(
                    None, self.competitor_store.similarity_search, query, k
                )
            )
        if self.serp_service is not None:
            tasks.append(self.serp_service.fetch_results(query, top_k=k))

        if not tasks:
            logger.warning("combined_retriever.no_sources")
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)
        documents: List[Document] = []
        for result in results:
            if isinstance(result, Exception):
                logger.exception("combined_retriever.source_failed", error=result)
                continue
            documents.extend(result)
        return documents

    def get_relevant_documents(self, query: str, k: int = 5) -> List[Document]:
        """Synchronous helper for compatibility with non-async workflows."""

        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.aget_relevant_documents(query, k=k))
        finally:
            loop.close()

