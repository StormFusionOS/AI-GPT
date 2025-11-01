"""Pydantic schemas for AI generated assets."""
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel


class MetaSuggestion(BaseModel):
    title: str
    description: str
    primary_keyword: str
    secondary_keywords: List[str]


class FAQItem(BaseModel):
    question: str
    answer: str


class JSONLD(BaseModel):
    data: Dict[str, Any]


class FeaturedSnippet(BaseModel):
    query: str
    snippet: str
    url: str
