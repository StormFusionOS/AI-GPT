"""Tests for the security hygiene endpoints and utilities."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.core import config as config_module
from app.db import DatabaseSession
from ops_api.routers import security


def _claims(role: str = "SEO_ENGINEER") -> dict[str, str]:
    return {"sub": "ops@example.com", "role": role}


@pytest.mark.usefixtures("override_settings")
def test_security_scan_detects_drift(
    db_session: DatabaseSession, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.php").write_text("<?php echo 'ok'; ?>\n")

    ops_dir = tmp_path / "ops"
    ops_dir.mkdir()
    target_file = ops_dir / "module.py"
    target_file.write_text("print('hello')\n")

    monkeypatch.setenv("OPS_INTEGRITY_PATHS", f"{plugin_dir},{ops_dir}")
    settings = config_module.get_settings()
    assert settings.integrity_paths == [str(plugin_dir), str(ops_dir)]

    initial = security.run_security_scan(claims=_claims(), session=db_session)
    assert initial.drift == [], f"unexpected drift: {[(item.path, item.reason) for item in initial.drift]}"
    baseline = db_session.get_file_integrity(str(ops_dir.resolve()))
    assert baseline is not None
    original_hash = baseline.sha256

    target_file.write_text("print('tampered')\n")

    follow_up = security.run_security_scan(claims=_claims(), session=db_session)
    changed_path = str(ops_dir.resolve())
    assert any(d.path == changed_path and d.reason == "hash_mismatch" for d in follow_up.drift), (
        original_hash,
        [
            (item.path, item.reason, item.expected_sha, item.observed_sha)
            for item in follow_up.drift
        ],
    )

    status = security.get_security_hygiene(claims=_claims(), session=db_session)
    assert status.last_scan is not None
    assert any(d.path == changed_path for d in status.drift)


@pytest.mark.usefixtures("override_settings")
def test_security_scan_requires_authorised_role(
    db_session: DatabaseSession, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPS_INTEGRITY_PATHS", str(tmp_path))
    settings = config_module.get_settings()
    assert settings.integrity_paths == [str(tmp_path)]

    with pytest.raises(Exception):
        security.run_security_scan(claims={"role": "VIEWER"}, session=db_session)
