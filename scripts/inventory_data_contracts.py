"""Generate the Phase 4 cross-store ownership and stable-identifier inventory."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import models  # noqa: E402
from backend.storage.data_contracts import build_contract_manifest  # noqa: E402


DEFAULT_JSON = ROOT / "reports/production-readiness/2026/phase-04/cp4-a-data-ownership-matrix.json"
DEFAULT_MARKDOWN = ROOT / "reports/production-readiness/2026/phase-04/cp4-a-data-ownership-matrix.md"


def _cell(value: object) -> str:
    return str(value or "-").replace("|", "\\|").replace("\n", " ")


def _render_markdown(manifest: dict[str, object]) -> str:
    logical = manifest["logical_data_contracts"]
    entities = manifest["postgresql_entities"]
    constraints = manifest["release_constraints"]
    lines = [
        "# CP4-A Cross-Store Data Ownership Matrix",
        "",
        "## Status",
        "",
        f"- Contract schema: `{manifest['schema_version']}`",
        f"- Captured: `{manifest['captured_at']}`",
        f"- PostgreSQL entities covered: **{manifest['postgresql_entity_count']}**",
        f"- Registry errors: **{len(manifest['validation_errors'])}**",
        f"- Production object-store authority: **{constraints['object_store_architecture']}**",
        "- SeaweedFS production selected: **No**",
        "- Managed coordinated backup authorized: **No**",
        "",
        "This matrix assigns exactly one authority to every current logical data",
        "class and records all materialized copies. A materialization never becomes",
        "authoritative merely because its service is reachable. Remaining durable",
        "target gaps are assigned to their owning later production-plan phases.",
        "",
        "## Logical data classes",
        "",
        "| Data class | Authority | Stable ID | Materializations | Transaction boundary | Compensation | Status |",
        "|---|---|---|---|---|---|---|",
    ]
    for contract in logical:
        lines.append(
            "| "
            + " | ".join(
                _cell(value)
                for value in (
                    contract["key"],
                    contract["authority"],
                    contract["stable_id"],
                    ", ".join(contract["materializations"]) or "none",
                    contract["transaction_boundary"],
                    contract["compensating_action"],
                    contract["implementation_status"],
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## PostgreSQL physical entities",
            "",
            "Every SQLAlchemy table is PostgreSQL-owned as a physical record. The",
            "logical matrix above separately identifies authoritative records and",
            "their graph, vector, cache, object, or file materializations.",
            "",
            "| Table | Stable primary identity |",
            "|---|---|",
        ]
    )
    for entity in entities:
        lines.append(f"| `{entity['table']}` | `{entity['stable_id_field']}` |")
    lines.extend(
        [
            "",
            "## Open implementation gaps exposed by the contract",
            "",
        ]
    )
    missing = [
        contract
        for contract in logical
        if contract["implementation_status"] != "implemented"
    ]
    for contract in missing:
        lines.append(
            f"- `{contract['key']}`: `{contract['implementation_status']}`."
        )
    lines.extend(
        [
            "",
            "## Required cross-store envelope",
            "",
            "Every outbox/reconciliation record must carry `entity_type`, stable",
            "`entity_id`, `schema_version`, `source_revision`, `correlation_id`, a",
            "timezone-aware `occurred_at`, and `payload_sha256`. Partial success stays",
            "visible and retryable until every required materialization confirms the",
            "same source revision and payload hash.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", dest="json_path", default=str(DEFAULT_JSON))
    parser.add_argument("--markdown", dest="markdown_path", default=str(DEFAULT_MARKDOWN))
    args = parser.parse_args()

    manifest = build_contract_manifest(models.db.metadata.tables)
    manifest["captured_at"] = datetime.now(UTC).isoformat()

    json_path = Path(args.json_path).expanduser().resolve()
    markdown_path = Path(args.markdown_path).expanduser().resolve()
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(_render_markdown(manifest), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "pass" if not manifest["validation_errors"] else "fail",
                "postgresql_entities": manifest["postgresql_entity_count"],
                "logical_data_contracts": len(manifest["logical_data_contracts"]),
                "validation_errors": manifest["validation_errors"],
                "json": str(json_path),
                "markdown": str(markdown_path),
            },
            indent=2,
        )
    )
    return 1 if manifest["validation_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
