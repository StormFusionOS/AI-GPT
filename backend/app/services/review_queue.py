"""In-memory review queue store and diff helpers for local development."""
from __future__ import annotations

"""In-memory review queue store and diff helpers for local usage."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Dict, Iterable, List

from fastapi import HTTPException


@dataclass
class ContentVersion:
    id: str
    content_id: str
    label: str
    author: str
    created_at: datetime
    body: str


@dataclass
class ReviewChange:
    id: str
    title: str
    module: str
    change_type: str
    status: str
    created_at: datetime
    submitted_by: str
    summary: str
    content_id: str
    current_version_id: str
    proposed_version_id: str
    metadata: Dict[str, str]
    last_reviewed_at: datetime | None = None
    last_reviewed_by: str | None = None
    history: List[Dict[str, str]] = field(default_factory=list)


_NOW = datetime.now(tz=UTC)

_CONTENT_VERSIONS: Dict[str, ContentVersion] = {
    'content-home-v1': ContentVersion(
        id='content-home-v1',
        content_id='home-page',
        label='Live Revision',
        author='Alex Morgan',
        created_at=_NOW - timedelta(days=14),
        body=(
            "<h1>Eco-Friendly Cleaning Services</h1>\n"
            "<p>River City Clean Co. provides sustainable commercial cleaning across Sacramento."\n"
            "We tailor plans for offices, warehouses, and medical facilities.</p>\n"
            "<p>Call us to schedule a walkthrough and estimate.</p>"
        ),
    ),
    'content-home-v2': ContentVersion(
        id='content-home-v2',
        content_id='home-page',
        label='AI Draft',
        author='AI Copilot',
        created_at=_NOW - timedelta(days=1, hours=3),
        body=(
            "<h1>Eco-Friendly Commercial Cleaning in Sacramento</h1>\n"
            "<p>River City Clean Co. delivers certified green cleaning for offices, medical suites, and industrial campuses."\n"
            "Our specialists design flexible plans with transparent pricing and measurable results.</p>\n"
            "<p>Book a walkthrough to receive a customized proposal within 24 hours.</p>"
        ),
    ),
    'schema-home-v1': ContentVersion(
        id='schema-home-v1',
        content_id='home-schema',
        label='Live Schema',
        author='Alex Morgan',
        created_at=_NOW - timedelta(days=10),
        body=(
            '{\n'
            '  "@context": "https://schema.org",\n'
            '  "@type": "LocalBusiness",\n'
            '  "name": "River City Clean Co.",\n'
            '  "address": {\n'
            '    "@type": "PostalAddress",\n'
            '    "streetAddress": "401 Market Street",\n'
            '    "addressLocality": "Sacramento",\n'
            '    "addressRegion": "CA",\n'
            '    "postalCode": "94203"\n'
            '  }\n'
            '}'
        ),
    ),
    'schema-home-v2': ContentVersion(
        id='schema-home-v2',
        content_id='home-schema',
        label='AI Recommendation',
        author='AI Copilot',
        created_at=_NOW - timedelta(hours=6),
        body=(
            '{\n'
            '  "@context": "https://schema.org",\n'
            '  "@type": "LocalBusiness",\n'
            '  "name": "River City Clean Co.",\n'
            '  "image": "https://rivercityclean.com/assets/hero.jpg",\n'
            '  "telephone": "+1-555-0100",\n'
            '  "address": {\n'
            '    "@type": "PostalAddress",\n'
            '    "streetAddress": "401 Market Street",\n'
            '    "addressLocality": "Sacramento",\n'
            '    "addressRegion": "CA",\n'
            '    "postalCode": "94203"\n'
            '  },\n'
            '  "sameAs": [\n'
            '    "https://www.facebook.com/rivercityclean",\n'
            '    "https://www.yelp.com/biz/river-city-clean"\n'
            '  ]\n'
            '}'
        ),
    ),
    'faq-v1': ContentVersion(
        id='faq-v1',
        content_id='faq-page',
        label='Published FAQ',
        author='Alex Morgan',
        created_at=_NOW - timedelta(days=7),
        body=(
            "<h2>How quickly can you start?</h2>\n"
            "<p>We begin new engagements within seven business days of signing.</p>\n"
            "<h2>Do you use eco-friendly products?</h2>\n"
            "<p>Yes, every cleaner is GreenSeal certified and safe for medical facilities.</p>"
        ),
    ),
    'faq-v2': ContentVersion(
        id='faq-v2',
        content_id='faq-page',
        label='AI FAQ Draft',
        author='AI Copilot',
        created_at=_NOW - timedelta(days=1),
        body=(
            "<h2>How soon can services start?</h2>\n"
            "<p>Most clients receive their onboarding visit within five business days.</p>\n"
            "<h2>What eco certifications do you carry?</h2>\n"
            "<p>Our products are EPA Safer Choice approved and compliant with medical-grade sanitation.</p>"
        ),
    ),
}


_REVIEW_CHANGES: Dict[str, ReviewChange] = {
    'chg-100': ReviewChange(
        id='chg-100',
        title='Homepage hero refresh',
        module='content',
        change_type='refresh_suggestions',
        status='pending',
        created_at=_NOW - timedelta(hours=5),
        submitted_by='seo_cycle',
        summary='Recommend updating hero copy to emphasize certified green cleaning.',
        content_id='home-page',
        current_version_id='content-home-v1',
        proposed_version_id='content-home-v2',
        metadata={'priority': 'high', 'pageUrl': 'https://rivercityclean.com/'},
    ),
    'chg-101': ReviewChange(
        id='chg-101',
        title='Add LocalBusiness schema enhancements',
        module='seo',
        change_type='schema_recommendation',
        status='pending',
        created_at=_NOW - timedelta(hours=2, minutes=40),
        submitted_by='seo_cycle',
        summary='Suggested schema includes image, telephone, and sameAs links.',
        content_id='home-schema',
        current_version_id='schema-home-v1',
        proposed_version_id='schema-home-v2',
        metadata={'priority': 'medium', 'pageUrl': 'https://rivercityclean.com/'},
    ),
    'chg-099': ReviewChange(
        id='chg-099',
        title='January FAQ refresh',
        module='content',
        change_type='faq_generation',
        status='approved',
        created_at=_NOW - timedelta(days=1, hours=3),
        submitted_by='seo_cycle',
        summary='FAQs approved and published to /faq.',
        content_id='faq-page',
        current_version_id='faq-v1',
        proposed_version_id='faq-v2',
        metadata={'priority': 'low', 'pageUrl': 'https://rivercityclean.com/faq'},
        last_reviewed_at=_NOW - timedelta(hours=1),
        last_reviewed_by='jordan@rivercityclean.com',
        history=[
            {
                'action': 'approved',
                'actor': 'jordan@rivercityclean.com',
                'note': 'Published to production',
                'timestamp': (_NOW - timedelta(hours=1)).isoformat(),
            }
        ],
    ),
}


def list_changes(status: str | None = None) -> list[ReviewChange]:
    """Return review changes optionally filtered by status."""

    items = list(_REVIEW_CHANGES.values())
    if status:
        lowered = status.lower()
        items = [item for item in items if item.status.lower() == lowered]
    items.sort(key=lambda change: change.created_at, reverse=True)
    return items


def get_change(change_id: str) -> ReviewChange:
    if change_id not in _REVIEW_CHANGES:
        raise HTTPException(status_code=404, detail='Change not found')
    return _REVIEW_CHANGES[change_id]


def update_change_status(change_id: str, status: str, actor: str, note: str | None = None) -> ReviewChange:
    change = get_change(change_id)
    change.status = status
    change.last_reviewed_at = datetime.now(tz=UTC)
    change.last_reviewed_by = actor
    if note:
        change.metadata = {**change.metadata, 'note': note}
    change.history.append(
        {
            'action': status,
            'actor': actor,
            'note': note or '',
            'timestamp': change.last_reviewed_at.isoformat(),
        }
    )
    return change


def get_version(version_id: str) -> ContentVersion:
    if version_id not in _CONTENT_VERSIONS:
        raise HTTPException(status_code=404, detail='Content version not found')
    return _CONTENT_VERSIONS[version_id]


def get_versions_for_content(content_id: str) -> Iterable[ContentVersion]:
    return [item for item in _CONTENT_VERSIONS.values() if item.content_id == content_id]


def resolve_diff(content_id: str, version_a: str, version_b: str) -> tuple[ContentVersion, ContentVersion]:
    versions = {item.id: item for item in get_versions_for_content(content_id)}
    if version_a not in versions:
        raise HTTPException(status_code=404, detail='Version A not found for content')
    if version_b not in versions:
        raise HTTPException(status_code=404, detail='Version B not found for content')
    return versions[version_a], versions[version_b]


__all__ = [
    'ContentVersion',
    'ReviewChange',
    'list_changes',
    'get_change',
    'update_change_status',
    'get_version',
    'get_versions_for_content',
    'resolve_diff',
]
