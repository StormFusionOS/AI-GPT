"""In-memory WordPress helpers for ops workflows."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class _PageState:
    meta: Dict[str, Any] = field(default_factory=dict)
    faqs: List[Dict[str, Any]] = field(default_factory=list)
    jsonld: Dict[str, Any] = field(default_factory=dict)
    links: List[Dict[str, Any]] = field(default_factory=list)


class WordPressSite:
    """Very small in-memory representation of WordPress content."""

    def __init__(self) -> None:
        self._pages: Dict[str, _PageState] = {}

    # -- helpers -----------------------------------------------------------------
    def reset(self) -> None:
        self._pages.clear()

    def seed_page(
        self,
        page_id: str,
        *,
        meta: Dict[str, Any] | None = None,
        faqs: List[Dict[str, Any]] | None = None,
        jsonld: Dict[str, Any] | None = None,
        links: List[Dict[str, Any]] | None = None,
    ) -> None:
        state = self._pages.setdefault(page_id, _PageState())
        if meta is not None:
            state.meta = dict(meta)
        if faqs is not None:
            state.faqs = [dict(item) for item in faqs]
        if jsonld is not None:
            state.jsonld = dict(jsonld)
        if links is not None:
            state.links = [dict(item) for item in links]

    def _state(self, page_id: str) -> _PageState:
        return self._pages.setdefault(page_id, _PageState())

    # -- queries ------------------------------------------------------------------
    def get_meta(self, page_id: str) -> Dict[str, Any]:
        return dict(self._state(page_id).meta)

    def get_faqs(self, page_id: str) -> List[Dict[str, Any]]:
        return [dict(item) for item in self._state(page_id).faqs]

    def get_jsonld(self, page_id: str) -> Dict[str, Any]:
        return dict(self._state(page_id).jsonld)

    def get_links(self, page_id: str) -> List[Dict[str, Any]]:
        return [dict(item) for item in self._state(page_id).links]

    # -- mutations ----------------------------------------------------------------
    def apply_meta(self, page_id: str, meta: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        state = self._state(page_id)
        before = dict(state.meta)
        state.meta = dict(meta)
        return before, dict(state.meta)

    def append_faq(self, page_id: str, faq: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        state = self._state(page_id)
        before = [dict(item) for item in state.faqs]
        state.faqs.append(dict(faq))
        return before, [dict(item) for item in state.faqs]

    def apply_jsonld(self, page_id: str, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        state = self._state(page_id)
        before = dict(state.jsonld)
        state.jsonld = dict(data)
        return before, dict(state.jsonld)

    def add_internal_link(self, page_id: str, link: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        state = self._state(page_id)
        before = [dict(item) for item in state.links]
        state.links.append(dict(link))
        return before, [dict(item) for item in state.links]


_SITE = WordPressSite()


def get_wordpress_site() -> WordPressSite:
    return _SITE


def reset_wordpress_site() -> None:
    _SITE.reset()

