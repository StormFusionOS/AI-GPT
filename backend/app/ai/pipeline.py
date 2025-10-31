"""Coordinated SEO intelligence workflows leveraging LangChain and Qdrant."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Protocol, Sequence

import structlog
from langchain.schema import Document

from .generators import (
    AnomalyAnalyzer,
    ContentRefresher,
    FAQGenerator,
    MetaDescriptionRewriter,
    SchemaInjector,
)
from .retriever import CombinedRetriever, QdrantVectorStoreManager

logger = structlog.get_logger(__name__)


class ContentSource(Protocol):
    """Adapter interface that returns new or updated documents for indexing."""

    async def fetch_new_documents(self) -> Sequence[Document]:
        ...


class ChangeLogRepository(Protocol):
    """Persistence port for change_log table."""

    async def create_change(
        self,
        *,
        module: str,
        change_type: str,
        details: str,
        status: str = "pending",
    ) -> None:
        ...


class AuditIssueRepository(Protocol):
    """Persistence port for audit_issues table."""

    async def create_issue(
        self,
        *,
        audit_id: int | None,
        description: str,
        severity: str,
    ) -> None:
        ...


class TaskLogger(Protocol):
    """Port to record task_logs entries."""

    async def log(
        self,
        *,
        task_name: str,
        status: str,
        detail: str,
    ) -> None:
        ...


@dataclass
class SEOCycleContext:
    """Context payload describing the workload for a cycle."""

    pages: Sequence[dict]
    symptoms: Sequence[dict]


async def update_vector_indexes(
    sources: Sequence[ContentSource],
    vector_managers: Sequence[QdrantVectorStoreManager],
) -> None:
    """Fetch new documents and upsert them into every configured vector store."""

    for source in sources:
        documents = await source.fetch_new_documents()
        if not documents:
            continue
        logger.info('seo_cycle.index', source=source.__class__.__name__, count=len(documents))
        for manager in vector_managers:
            manager.upsert_documents(documents)


async def run_generators_for_page(
    *,
    page: dict,
    retriever: CombinedRetriever,
    faq_generator: FAQGenerator,
    meta_rewriter: MetaDescriptionRewriter,
    refresher: ContentRefresher,
    schema_injector: SchemaInjector,
    change_log_repo: ChangeLogRepository,
) -> None:
    """Execute page specific generators and enqueue results for review."""

    topic = page.get("title", page.get("url", "Unknown Page"))
    docs = await retriever.aget_relevant_documents(topic, k=5)

    faq_payload = await faq_generator.agenerate(topic=topic, context_docs=docs)
    change_log_repo_task = change_log_repo.create_change(
        module="content",
        change_type="faq_generation",
        details=faq_payload.model_dump_json(indent=2),
    )

    meta_payload = await meta_rewriter.arewrite(
        title=topic,
        current_description=page.get("meta_description", ""),
        keywords=page.get("keywords", []),
        context_docs=docs,
    )
    schema_payload = await schema_injector.arecommend(
        page_metadata=page.get("metadata", ""),
        faq_context=faq_payload.faqs,
    )
    refresh_payload = await refresher.arefresh(
        title=topic,
        content=page.get("body", ""),
        competitor_context=docs,
    )

    await asyncio.gather(
        change_log_repo_task,
        change_log_repo.create_change(
            module="seo",
            change_type="meta_description",
            details=meta_payload.model_dump_json(indent=2),
        ),
        change_log_repo.create_change(
            module="seo",
            change_type="schema_recommendation",
            details=schema_payload.model_dump_json(indent=2),
        ),
        change_log_repo.create_change(
            module="content",
            change_type="refresh_suggestions",
            details=refresh_payload.model_dump_json(indent=2),
        ),
    )


async def handle_anomalies(
    *,
    symptoms: Sequence[dict],
    anomaly_analyzer: AnomalyAnalyzer,
    retriever: CombinedRetriever,
    audit_repo: AuditIssueRepository,
) -> None:
    """Run anomaly analysis and log resulting audit issues."""

    for symptom in symptoms:
        url = symptom.get("url", "")
        docs = await retriever.aget_relevant_documents(url, k=5)
        insight = await anomaly_analyzer.aanalyze(
            url=url,
            symptoms=symptom.get("description", ""),
            metrics=symptom.get("metrics", ""),
            competitor_notes=docs,
        )
        await audit_repo.create_issue(
            audit_id=None,
            description=f"Anomaly detected for {url}: {insight.hypothesis}",
            severity="high",
        )


async def process_seo_cycle(
    *,
    context: SEOCycleContext,
    retriever: CombinedRetriever,
    vector_managers: Sequence[QdrantVectorStoreManager],
    sources: Sequence[ContentSource],
    faq_generator: FAQGenerator,
    meta_rewriter: MetaDescriptionRewriter,
    refresher: ContentRefresher,
    schema_injector: SchemaInjector,
    anomaly_analyzer: AnomalyAnalyzer,
    change_log_repo: ChangeLogRepository,
    audit_repo: AuditIssueRepository,
    task_logger: TaskLogger,
) -> None:
    """End-to-end SEO cycle: index, analyze, and record recommendations."""

    logger.info("seo_cycle.start")
    await task_logger.log(task_name="seo_cycle", status="running", detail="cycle started")

    await update_vector_indexes(sources, vector_managers)

    page_tasks = [
        run_generators_for_page(
            page=page,
            retriever=retriever,
            faq_generator=faq_generator,
            meta_rewriter=meta_rewriter,
            refresher=refresher,
            schema_injector=schema_injector,
            change_log_repo=change_log_repo,
        )
        for page in context.pages
    ]
    await asyncio.gather(*page_tasks)
    await handle_anomalies(
        symptoms=context.symptoms,
        anomaly_analyzer=anomaly_analyzer,
        retriever=retriever,
        audit_repo=audit_repo,
    )

    await task_logger.log(task_name="seo_cycle", status="completed", detail="cycle finished")
    logger.info("seo_cycle.complete")


__all__ = [
    "SEOCycleContext",
    "process_seo_cycle",
    "update_vector_indexes",
]




# Example usage (pseudo-code)
# ----------------------------
# async def example():
#     retriever = CombinedRetriever(internal_store=internal_manager)
#     await process_seo_cycle(
#         context=SEOCycleContext(pages=[{"url": "https://example.com"}], symptoms=[]),
#         retriever=retriever,
#         vector_managers=[internal_manager],
#         sources=[crawler_source],
#         faq_generator=faq_generator,
#         meta_rewriter=meta_rewriter,
#         refresher=content_refresher,
#         schema_injector=schema_injector,
#         anomaly_analyzer=anomaly_analyzer,
#         change_log_repo=change_repo,
#         audit_repo=audit_repo,
#         task_logger=task_logger,
#     )
