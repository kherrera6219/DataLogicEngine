"""Generate the Phase 4 live migration and supported-upgrade inventory."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.storage.migration_inventory import build_migration_inventory

DEFAULT_JSON = (
    ROOT / "reports/production-readiness/2026/phase-04/cp4-b-migration-inventory.json"
)
DEFAULT_MARKDOWN = (
    ROOT / "reports/production-readiness/2026/phase-04/cp4-b-migration-inventory.md"
)


def _cell(value: object) -> str:
    return str(value or "-").replace("|", "\\|").replace("\n", " ")


def _render_markdown(inventory: dict[str, object]) -> str:
    alembic = inventory["alembic"]
    constraints = inventory["release_constraints"]
    lines = [
        "# CP4-B Migration and Supported-Upgrade Inventory",
        "",
        "## Status",
        "",
        f"- Inventory schema: `{inventory['schema_version']}`",
        f"- Captured: `{inventory['captured_at']}`",
        f"- Production migration ready: **{'Yes' if inventory['production_migration_ready'] else 'No'}**",
        f"- Alembic revisions: **{alembic['revision_count']}**",
        f"- Alembic base/head: `{', '.join(alembic['bases'])}` / `{', '.join(alembic['heads'])}`",
        f"- Alembic graph errors: **{len(alembic['errors'])}**",
        f"- Managed coordinated backup available: **{'Yes' if constraints['coordinated_backup_available'] else 'No'}**",
        "",
        "The PostgreSQL Alembic graph is a single linear chain. The startup migration",
        "coordinator probes every retained store before readiness, records per-store",
        "versions, requires verified coordinated backup before destructive work, and",
        "fails closed on newer or unsupported data. Legacy `db.create_all()` remains",
        "a development helper and is not the production coordinator.",
        "",
        "## Store migration surfaces",
        "",
        "| Surface | Target version | Version probe | Forward migration | Rollback policy | Status | Blocker |",
        "|---|---|---|---|---|---|---|",
    ]
    for surface in inventory["surfaces"]:
        lines.append(
            "| "
            + " | ".join(
                _cell(value)
                for value in (
                    surface["key"],
                    surface["target_version"],
                    surface["version_probe"],
                    surface["forward_migration"],
                    surface["rollback_policy"],
                    surface["status"],
                    surface["blocker"],
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Supported upgrade sources",
            "",
        ]
    )
    for version in inventory["supported_upgrade_sources"]:
        lines.append(
            f"- `{version}` retained-data input is in scope; its populated upgrade,"
            " uninstall/reinstall, rollback, and clean-restore matrix is not yet passed."
        )
    lines.extend(["", "## Blocking gaps", ""])
    for blocker in inventory["blockers"]:
        lines.append(f"- `{blocker}`")
    lines.extend(
        [
            "",
            "## Release constraints",
            "",
            "- The production capability authority is an app-owned S3-compatible",
            "  object store; the legacy `minio` migration key is retained for",
            "  persisted upgrade compatibility.",
            "- SeaweedFS 4.40-dle.1 is selected for rebuilt installed qualification;",
            "  production approval remains false until the installed gates pass.",
            "- Startup against a newer incompatible data version must fail closed.",
            "- Partial store migration must remain visible and rollback/retryable.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", dest="json_path", default=str(DEFAULT_JSON))
    parser.add_argument(
        "--markdown", dest="markdown_path", default=str(DEFAULT_MARKDOWN)
    )
    args = parser.parse_args()

    inventory = build_migration_inventory(ROOT)
    inventory["captured_at"] = datetime.now(UTC).isoformat()
    json_path = Path(args.json_path).expanduser().resolve()
    markdown_path = Path(args.markdown_path).expanduser().resolve()
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(_render_markdown(inventory), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "inventory_complete",
                "production_migration_ready": inventory["production_migration_ready"],
                "alembic_revisions": inventory["alembic"]["revision_count"],
                "alembic_errors": inventory["alembic"]["errors"],
                "blockers": inventory["blockers"],
                "json": str(json_path),
                "markdown": str(markdown_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
