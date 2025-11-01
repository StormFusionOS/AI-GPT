"""Pre-commit helper ensuring migrations accompany model changes."""
from __future__ import annotations

import sys
from pathlib import Path

WATCH_CONFIG = {
    "crm": {
        "models": {Path("crm_api/app/db_models.py")},
        "versions_dir": Path("crm_api/alembic/versions"),
    },
    "ops": {
        "models": {Path("ops_api/app/db_models.py")},
        "versions_dir": Path("ops_api/alembic/versions"),
    },
}


def main(argv: list[str]) -> int:
    if not argv:
        return 0

    changed = {Path(arg) for arg in argv}
    exit_code = 0

    for service, cfg in WATCH_CONFIG.items():
        model_paths = cfg["models"]
        touched_models = any(path in model_paths for path in changed)
        if not touched_models:
            continue
        has_migration = any(path.is_relative_to(cfg["versions_dir"]) for path in changed)
        if not has_migration:
            print(
                f"ERROR: {service} models were modified without a matching migration in {cfg['versions_dir']}",
                file=sys.stderr,
            )
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
