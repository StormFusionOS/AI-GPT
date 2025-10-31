"""LLM powered SEO content generation utilities."""
from __future__ import annotations

import asyncio
from typing import List, Optional, Sequence

import structlog
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from pydantic import BaseModel, Field

from .retriever import CombinedRetriever
from .utils import LLMJSONValidator

logger = structlog.get_logger(__name__)


class FAQItem(BaseModel):
    question: str = Field(..., description="FAQ question")
    answer: str = Field(..., description="Detailed answer for the question")


class FAQPayload(BaseModel):
    faqs: List[FAQItem]


class MetaDescriptionSuggestion(BaseModel):
    title: str
    meta_description: str = Field(..., max_length=160)


class ContentRefreshSuggestion(BaseModel):
    summary: str
    sections_to_update: List[str]
    new_content: Optional[str] = None


class SchemaRecommendation(BaseModel):
    schema_type: str
    json_ld: str = Field(..., description="Valid JSON-LD script suggestion")


class AnomalyInsight(BaseModel):
    hypothesis: str
    potential_causes: List[str]
    recommended_actions: List[str]


FAQ_PROMPT = PromptTemplate.from_template(
    """You are an expert SEO content strategist. Using the context below, generate
    a JSON object with the key "faqs" containing exactly {faq_count} items.
    Each item must have "question" and "answer" fields with rich detail.

    Context:
    {context}

    Topic or prompt: {topic}

    Respond with valid JSON only.
    """
)

META_DESCRIPTION_PROMPT = PromptTemplate.from_template(
    """You are an SEO optimization assistant. Rewrite the meta description to
    improve click-through rate while keeping it under 160 characters.

    Page title: {title}
    Current description: {current_description}
    Target keywords: {keywords}
    Content excerpt: {context}

    Return valid JSON with keys "title" and "meta_description".
    """
)

CONTENT_REFRESH_PROMPT = PromptTemplate.from_template(
    """You audit existing content and propose refreshes. Analyze the article and
    outline sections needing updates. Suggest new content if relevant.

    Article title: {title}
    Current content: {content}
    Recent competitor highlights: {competitor_context}

    Return JSON with keys:
    - summary (string)
    - sections_to_update (array of strings)
    - new_content (string, optional)
    """
)

SCHEMA_PROMPT = PromptTemplate.from_template(
    """You are a structured data expert. Determine the most relevant Schema.org
    markup for the page. If multiple apply, prioritize the most impactful.

    Page metadata:
    {page_metadata}

    FAQ context:
    {faq_context}

    Respond with JSON containing:
    - schema_type: string name of the schema
    - json_ld: JSON-LD string representation.
    Ensure json_ld is valid JSON and can be embedded in a <script type="application/ld+json"> tag.
    """
)

ANOMALY_PROMPT = PromptTemplate.from_template(
    """You analyze SEO performance anomalies. Review the metrics and hypothesize
    reasons for the change, then propose next actions.

    Page URL: {url}
    Symptoms: {symptoms}
    Performance metrics snapshot: {metrics}
    Competitor notes: {competitor_notes}

    Return JSON with keys:
    - hypothesis
    - potential_causes (array of strings)
    - recommended_actions (array of strings)
    """
)


class BaseGenerator:
    """Common behaviour for generator classes."""

    def __init__(self, chain: LLMChain, validator: LLMJSONValidator) -> None:
        self.chain = chain
        self.validator = validator

    async def arun(self, **kwargs) -> BaseModel:
        logger.info("generator.run", generator=self.__class__.__name__)
        raw = await self.chain.arun(**kwargs)
        return self.validator.parse(raw)

    def run(self, **kwargs) -> BaseModel:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.arun(**kwargs))
        raise RuntimeError('Cannot call run() inside an active event loop; await arun() instead.')


class FAQGenerator(BaseGenerator):
    """Generate FAQ question/answer pairs for a topic."""

    def __init__(
        self,
        chain: LLMChain,
        validator: Optional[LLMJSONValidator] = None,
        retriever: Optional[CombinedRetriever] = None,
    ) -> None:
        validator = validator or LLMJSONValidator(FAQPayload)
        super().__init__(chain, validator)
        self.retriever = retriever

    async def agenerate(
        self, topic: str, context_docs: Optional[Sequence[Document]] = None, faq_count: int = 5
    ) -> FAQPayload:
        if context_docs is None and self.retriever is not None:
            context_docs = await self.retriever.aget_relevant_documents(topic, k=faq_count)
        context = "\n".join(doc.page_content for doc in context_docs or [])
        payload = await self.arun(topic=topic, context=context, faq_count=faq_count)
        return payload  # type: ignore[return-value]

    def generate(
        self, topic: str, context_docs: Optional[Sequence[Document]] = None, faq_count: int = 5
    ) -> FAQPayload:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.agenerate(topic=topic, context_docs=context_docs, faq_count=faq_count))
        raise RuntimeError('Cannot call generate() inside an active event loop; await agenerate() instead.')


class MetaDescriptionRewriter(BaseGenerator):
    """Rewrite meta descriptions using contextual information."""

    async def arewrite(
        self,
        title: str,
        current_description: str,
        keywords: Sequence[str],
        context_docs: Optional[Sequence[Document]] = None,
    ) -> MetaDescriptionSuggestion:
        context = "\n".join(doc.page_content for doc in context_docs or [])
        payload = await self.arun(
            title=title,
            current_description=current_description,
            keywords=", ".join(keywords),
            context=context,
        )
        return payload  # type: ignore[return-value]


class ContentRefresher(BaseGenerator):
    """Analyze content and surface refresh opportunities."""

    async def arefresh(
        self,
        title: str,
        content: str,
        competitor_context: Optional[Sequence[Document]] = None,
    ) -> ContentRefreshSuggestion:
        context = "\n".join(doc.page_content for doc in competitor_context or [])
        payload = await self.arun(title=title, content=content, competitor_context=context)
        return payload  # type: ignore[return-value]


class SchemaInjector(BaseGenerator):
    """Recommend structured data for a page."""

    async def arecommend(
        self,
        page_metadata: str,
        faq_context: Optional[Sequence[FAQItem]] = None,
    ) -> SchemaRecommendation:
        faq_text = "\n".join(f"Q: {faq.question}\nA: {faq.answer}" for faq in faq_context or [])
        payload = await self.arun(page_metadata=page_metadata, faq_context=faq_text)
        return payload  # type: ignore[return-value]


class AnomalyAnalyzer(BaseGenerator):
    """Produce hypotheses for SEO performance anomalies."""

    async def aanalyze(
        self,
        url: str,
        symptoms: str,
        metrics: str,
        competitor_notes: Optional[Sequence[Document]] = None,
    ) -> AnomalyInsight:
        competitor_summary = "\n".join(doc.page_content for doc in competitor_notes or [])
        payload = await self.arun(
            url=url,
            symptoms=symptoms,
            metrics=metrics,
            competitor_notes=competitor_summary,
        )
        return payload  # type: ignore[return-value]


def build_default_generators(
    faq_chain: LLMChain,
    meta_chain: LLMChain,
    refresh_chain: LLMChain,
    schema_chain: LLMChain,
    anomaly_chain: LLMChain,
    retriever: Optional[CombinedRetriever] = None,
) -> dict[str, BaseGenerator]:
    """Convenience factory returning generator instances with shared retriever."""

    return {
        "faq": FAQGenerator(faq_chain, validator=LLMJSONValidator(FAQPayload), retriever=retriever),
        "meta": MetaDescriptionRewriter(meta_chain, LLMJSONValidator(MetaDescriptionSuggestion)),
        "refresh": ContentRefresher(refresh_chain, LLMJSONValidator(ContentRefreshSuggestion)),
        "schema": SchemaInjector(schema_chain, LLMJSONValidator(SchemaRecommendation)),
        "anomaly": AnomalyAnalyzer(anomaly_chain, LLMJSONValidator(AnomalyInsight)),
    }


__all__ = [
    "FAQGenerator",
    "MetaDescriptionRewriter",
    "ContentRefresher",
    "SchemaInjector",
    "AnomalyAnalyzer",
    "FAQ_PROMPT",
    "META_DESCRIPTION_PROMPT",
    "CONTENT_REFRESH_PROMPT",
    "SCHEMA_PROMPT",
    "ANOMALY_PROMPT",
    "build_default_generators",
    "FAQItem",
    "FAQPayload",
    "MetaDescriptionSuggestion",
    "ContentRefreshSuggestion",
    "SchemaRecommendation",
    "AnomalyInsight",
]

