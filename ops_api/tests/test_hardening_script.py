"""Tests for the hardening shell script in dry-run mode."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_hardening_script_emits_expected_commands(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "hardening.sh"
    env = os.environ.copy()
    env["HARDENING_DRY_RUN"] = "1"
    env["HARDENING_ETC_DIR"] = str(tmp_path / "etc")
    result = subprocess.run(
        ["bash", str(script)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    output = result.stdout
    assert "RUN:ufw --force enable" in output
    assert "RUN:ufw allow 22/tcp" in output
    assert "RUN:ufw allow 80/tcp" in output
    assert "RUN:ufw allow 443/tcp" in output

    second = subprocess.run(
        ["bash", str(script)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    assert second.returncode == 0
