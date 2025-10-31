"""Utility functions to expose AI prompt templates for manual execution."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Dict

from fastapi import HTTPException
from app.ai.generators import (
    FAQGenerator,
    MetaDescriptionRewriter,
    ContentRefresher,
    SchemaInjector,
    AnomalyAnalyzer,
)
from app.ai.retriever import CombinedRetriever

# LangChain integrations are heavy; for local development we provide
# deterministic fallbacks. Real deployments can wire in production LLM
# instances using dependency injection when the API layer is adapted.

_PROMPT_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    'faq_generator': {
        'label': 'FAQ Generator',
        'description': 'Create intent-focused FAQs for a page or topic.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'topic': {'type': 'string'},
                'context': {'type': 'string'},
            },
            'required': ['topic', 'context'],
        },
    },
    'meta_description': {
        'label': 'Meta Description Rewriter',
        'description': 'Optimize a meta description for CTR and keyword coverage.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'title': {'type': 'string'},
                'currentDescription': {'type': 'string'},
                'keywords': {'type': 'array', 'items': {'type': 'string'}},
                'context': {'type': 'string'},
            },
            'required': ['title', 'currentDescription'],
        },
    },
    'schema_recommendation': {
        'label': 'Schema Recommender',
        'description': 'Suggest JSON-LD markup for a page based on content cues.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'metadata': {'type': 'string'},
                'faqContext': {'type': 'string'},
            },
            'required': ['metadata'],
        },
    },
    'content_refresh': {
        'label': 'Content Refresher',
        'description': 'Highlight stale sections and suggest refreshed material.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'title': {'type': 'string'},
                'content': {'type': 'string'},
                'competitorNotes': {'type': 'string'},
            },
            'required': ['title', 'content'],
        },
    },
    'anomaly_analysis': {
        'label': 'Anomaly Analyzer',
        'description': 'Explain sudden ranking or traffic changes with hypotheses.',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'url': {'type': 'string'},
                'symptoms': {'type': 'string'},
                'metrics': {'type': 'string'},
                'competitorNotes': {'type': 'string'},
            },
            'required': ['url', 'symptoms'],
        },
    },
}


def list_prompts() -> list[dict[str, Any]]:
    return [
        {'name': name, **definition}
        for name, definition in sorted(_PROMPT_DEFINITIONS.items(), key=lambda item: item[1]['label'])
    ]


async def run_prompt(
    *,
    prompt: str,
    parameters: Dict[str, Any],
    retriever: CombinedRetriever | None = None,
) -> dict[str, Any]:
    """Execute a supported prompt returning structured output."""

    executed_at = datetime.now(tz=UTC)

    _ = retriever  # retriever may be injected in production deployments.

    if prompt == 'faq_generator':
        _ = FAQGenerator  # reference to avoid unused-import warnings in stub implementations
        faqs = parameters.get('context', '').split('\n')[:2] or [parameters.get('context', '')]
        payload = {
            'faqs': [
                {
                    'question': f"What should I know about {parameters.get('topic', 'this topic')}?",
                    'answer': paragraph.strip() or 'Provide updated context to improve this answer.',
                }
                for paragraph in faqs
                if paragraph
            ]
        }
        return {
            'prompt': prompt,
            'executedAt': executed_at,
            'output': payload,
            'metadata': {'model': 'mock-generator', 'note': 'Deterministic local output'},
        }

    if prompt == 'meta_description':
        _ = MetaDescriptionRewriter
        title = parameters.get('title', 'Untitled Page')
        description = parameters.get('currentDescription', '')
        keywords = parameters.get('keywords', [])
        optimized = f"{title} – {description[:80]}".strip()
        if keywords:
            optimized = f"{optimized} | {'/'.join(keywords[:2])}"
        return {
            'prompt': prompt,
            'executedAt': executed_at,
            'output': {'title': title, 'meta_description': optimized[:155]},
            'metadata': {'model': 'mock-generator'},
        }

    if prompt == 'schema_recommendation':
        _ = SchemaInjector
        metadata = parameters.get('metadata', '')
        faq_context = parameters.get('faqContext', '')
        schema = {
            '@context': 'https://schema.org',
            '@type': 'FAQPage' if faq_context else 'WebPage',
            'about': metadata[:120],
        }
        return {
            'prompt': prompt,
            'executedAt': executed_at,
            'output': {'schema_type': schema['@type'], 'json_ld': schema},
            'metadata': {'model': 'mock-generator'},
        }

    if prompt == 'content_refresh':
        _ = ContentRefresher
        content = parameters.get('content', '')
        sections = [section.strip() for section in content.split('\n\n') if section.strip()]
        return {
            'prompt': prompt,
            'executedAt': executed_at,
            'output': {
                'summary': 'Focus on refreshing statistics and testimonials.',
                'sections_to_update': sections[:3],
                'new_content': 'Insert 2025 performance metrics and recent client quotes.',
            },
            'metadata': {'model': 'mock-generator'},
        }

    if prompt == 'anomaly_analysis':
        _ = AnomalyAnalyzer
        return {
            'prompt': prompt,
            'executedAt': executed_at,
            'output': {
                'hypothesis': 'Competitor expanded content and improved internal linking.',
                'potential_causes': [
                    'Competitor updated page within the last 48 hours',
                    'Our page has declining crawl frequency',
                ],
                'recommended_actions': [
                    'Publish refreshed content and request reindex',
                    'Add supporting internal links from related service pages',
                ],
            },
            'metadata': {'model': 'mock-generator'},
        }

    raise HTTPException(status_code=400, detail=f'Unsupported prompt {prompt!r}')


__all__ = ['list_prompts', 'run_prompt']
