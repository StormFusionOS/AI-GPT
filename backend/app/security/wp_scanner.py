"""WordPress plugin auditing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import WordPressSiteConfig, settings


@dataclass(slots=True)
class PluginFinding:
    """Represents the state of a single WordPress plugin."""

    slug: str
    name: str
    installed_version: str
    latest_version: str | None
    status: str
    severity: str
    notes: str | None = None


@dataclass(slots=True)
class SiteSecurityReport:
    """Summary of plugin posture for a WordPress site."""

    site: str
    base_url: str
    checked_at: datetime
    plugins: list[PluginFinding]
    errors: list[str]

    def to_payload(self) -> dict[str, Any]:
        return {
            'site': self.site,
            'base_url': self.base_url,
            'checked_at': self.checked_at.isoformat(),
            'plugins': [plugin.__dict__ for plugin in self.plugins],
            'errors': self.errors,
        }


SECURITY_PLUGIN_SLUGS = {'wordfence', 'sucuri-scanner', 'ithemes-security-pro'}


async def _fetch_plugins(client: httpx.AsyncClient, site: WordPressSiteConfig) -> list[dict[str, Any]]:
    url = f"{site.base_url.rstrip('/')}/wp-json/wp/v2/plugins"
    response = await client.get(url, auth=(site.username, site.application_password), timeout=20)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict) and 'plugins' in data:
        data = data['plugins']
    if not isinstance(data, list):
        raise ValueError('Unexpected plugin payload')
    return data


async def _fetch_latest_version(client: httpx.AsyncClient, slug: str) -> str | None:
    endpoint = 'https://api.wordpress.org/plugins/info/1.2/'
    params = {
        'action': 'plugin_information',
        'request[slug]': slug,
        'request[fields][versions]': 0,
    }
    response = await client.get(endpoint, params=params, timeout=20)
    if response.status_code != 200:
        return None
    payload = response.json()
    if not isinstance(payload, dict):
        return None
    version = payload.get('version')
    return str(version) if version else None


def _determine_status(installed: str, latest: str | None) -> tuple[str, str]:
    if latest is None:
        return 'unknown', 'warning'
    if installed == latest:
        return 'ok', 'info'
    return 'outdated', 'critical'


async def scan_wordpress_plugins() -> list[SiteSecurityReport]:
    """Audit configured WordPress sites for outdated or missing plugins."""

    sites = settings.wordpress_sites
    if not sites:
        return []

    reports: list[SiteSecurityReport] = []
    async with httpx.AsyncClient() as client:
        cache: dict[str, str | None] = {}
        for site in sites:
            checked_at = datetime.now(tz=UTC)
            findings: list[PluginFinding] = []
            errors: list[str] = []
            try:
                plugins = await _fetch_plugins(client, site)
            except Exception as exc:  # pragma: no cover - network failure path
                errors.append(f'Failed to fetch plugins: {exc}')
                reports.append(
                    SiteSecurityReport(
                        site=site.name,
                        base_url=str(site.base_url),
                        checked_at=checked_at,
                        plugins=[],
                        errors=errors,
                    )
                )
                continue

            seen_security_plugin = False
            for plugin in plugins:
                slug = str(plugin.get('textdomain') or plugin.get('plugin') or plugin.get('slug') or '')
                if '/' in slug:
                    slug = slug.split('/', 1)[0]
                name = str(plugin.get('name') or slug)
                version = str(plugin.get('version') or 'unknown')

                if slug not in cache:
                    try:
                        cache[slug] = await _fetch_latest_version(client, slug)
                    except Exception:  # pragma: no cover - network failure path
                        cache[slug] = None
                latest = cache[slug]
                status, severity = _determine_status(version, latest)

                findings.append(
                    PluginFinding(
                        slug=slug,
                        name=name,
                        installed_version=version,
                        latest_version=latest,
                        status=status,
                        severity=severity,
                        notes=None if status == 'ok' else 'Update recommended',
                    )
                )

                if slug in SECURITY_PLUGIN_SLUGS:
                    seen_security_plugin = True

            if not seen_security_plugin:
                findings.append(
                    PluginFinding(
                        slug='security-suite',
                        name='Security Plugin',
                        installed_version='missing',
                        latest_version=None,
                        status='missing',
                        severity='warning',
                        notes='Install a Web Application Firewall plugin such as Wordfence.',
                    )
                )

            reports.append(
                SiteSecurityReport(
                    site=site.name,
                    base_url=str(site.base_url),
                    checked_at=checked_at,
                    plugins=findings,
                    errors=errors,
                )
            )

    return reports

