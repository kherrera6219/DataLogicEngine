#!/usr/bin/env python3
"""Verify the Phase 16 CP16-C engineering/assurance documentation checkpoint."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from generate_documentation_authority import DEFAULT_CONFIG, ROOT, load_authority
    from verify_doc_authority import parse_controlled_header
except ModuleNotFoundError:  # Imported through the scripts namespace in tests.
    from scripts.generate_documentation_authority import (
        DEFAULT_CONFIG,
        ROOT,
        load_authority,
    )
    from scripts.verify_doc_authority import parse_controlled_header


DEFAULT_REPORT = (
    ROOT
    / "reports"
    / "production-readiness"
    / "2026"
    / "phase-16"
    / "engineering-assurance-document-verification.json"
)
TARGETS = {
    "docs/DATA_ARCHITECTURE.md": {
        "sources": {
            "docs/DATABASE_SCHEMA.md",
            "docs/DATA_AT_REST_AND_KEY_MANAGEMENT.md",
            "docs/DATA_CLASSIFICATION_REGISTER.md",
            "docs/LOCAL_USAGE_LEDGER_CONTRACT.md",
            "docs/MIGRATION_SUPPORT_MATRIX.md",
            "docs/diagrams/07_data_storage_and_memory_architecture.md",
            "docs/adr/ADR-0004-seaweedfs-replacement-qualification.md",
            "docs/adr/ADR-0006-memory-authority-and-trust-boundary.md",
        },
        "markers": {
            "Store responsibility map",
            "Classification and protection",
            "Migration and schema rules",
            "Backup, restore, and deletion",
            "SeaweedFS 4.40-dle.1 for rebuilt installed qualification",
        },
    },
    "docs/INTERFACE_INTEGRATION.md": {
        "sources": {
            "docs/API.md",
            "docs/API_VERSIONING.md",
            "docs/AUTH_DECORATORS.md",
            "docs/GATEWAY_COMPATIBILITY.md",
            "docs/MCP_INTEGRATION.md",
            "docs/adr/ADR-0002-pq-grpc-transport.md",
            "docs/adr/ADR-0005-external-gateway-boundary.md",
            "docs/adr/ADR-0008-governed-mcp-connector-boundary.md",
        },
        "markers": {
            "/api/v1/*",
            "Authentication and authorization",
            "Governed request contract",
            "Native request modes",
            "MCP integration contract",
            "private_windows_gateway",
        },
    },
    "docs/SECURITY_ARCHITECTURE.md": {
        "sources": {
            "docs/SECURITY.md",
            "docs/THREAT_MODEL.md",
            "docs/CIS_BENCHMARKS.md",
            "docs/SSL_CONFIGURATION.md",
            "docs/diagrams/06_local_first_security_model.md",
        },
        "markers": {
            "Trust boundaries",
            "Protected assets",
            "Governed AI and content controls",
            "Release and update trust",
            "Principal threats and controls",
            "Alert 389 is fixed",
        },
    },
    "docs/SOFTWARE_LIFECYCLE_PLAN.md": {
        "sources": {
            "DEVELOPMENT.md",
            "docs/AI_PRODUCTION_DOCUMENTATION_BASELINE.md",
            "docs/BRANCH_PROTECTION_POLICY.md",
            "docs/DOCUMENTATION_STANDARDS.md",
            "docs/DOCUMENTATION_VERSIONING.md",
            "docs/SDLC_SSDF_MAPPING.md",
        },
        "markers": {
            "Authoritative configuration",
            "Change lifecycle",
            "Verification pipeline",
            "Release lifecycle",
            "Documentation lifecycle",
            "Maintenance and retirement",
        },
    },
    "docs/MAINTENANCE_DISASTER_RECOVERY.md": {
        "sources": set(),
        "markers": {
            "Recovery objectives",
            "Protected recovery set",
            "Backup procedure",
            "Restore procedure",
            "Failure and rollback",
            "Acceptance record",
        },
    },
    "docs/REQUIREMENTS_TRACEABILITY.md": {
        "sources": {
            "docs/DOCUMENTATION_COVERAGE_MATRIX.md",
            "docs/diagrams/02_research_to_code_traceability.md",
        },
        "markers": {
            "DLE-FR-001",
            "DLE-DR-001",
            "DLE-SR-001",
            "DLE-PR-001",
            "DLE-AI-001",
            "DLE-QR-001",
            "All 29 product requirement IDs",
        },
    },
    "docs/VERIFICATION_VALIDATION_REPORT.md": {
        "sources": {
            "TESTING.md",
            "docs/TESTING.md",
            "docs/PRODUCTION_READINESS.md",
            "docs/evaluation/HUMAN_REVIEW_RUBRIC.md",
            "docs/diagrams/08_testing_validation_and_release_governance.md",
        },
        "markers": {
            "Verification levels",
            "Test domains and acceptance",
            "Current candidate evidence",
            "Human and independent validation",
            "24-hour stress",
            "Production/public release is **NO-GO**",
        },
    },
    "docs/KA_TRUTHCORE_VALIDATION_DOSSIER.md": {
        "sources": {
            "docs/KNOWLEDGE_ALGORITHM_CATALOG.md",
            "docs/ip/dsqp_technical_disclosure.md",
            "docs/diagrams/03_ai_reasoning_sequence.md",
            "docs/diagrams/04_17_axis_coordinate_model.md",
            "docs/diagrams/05_truth_engine_architecture.md",
            "docs/diagrams/10_dsqp_persona_construction_architecture.md",
            "docs/adr/ADR-0007-authoritative-simulation-engine.md",
        },
        "markers": {
            "current executable registry exposes 125 IDs",
            "enabled 11",
            "TruthCore and evidence model",
            "Phase 6 checkpoint evidence",
            "Evaluation protocol",
            "Human review",
        },
    },
    "docs/PRIVACY_IMPACT_ASSESSMENT.md": {
        "sources": set(),
        "markers": {
            "Assessment status and scope",
            "Data inventory",
            "Data flows and recipients",
            "Retention and deletion",
            "Risk assessment",
            "Required approvals before production",
        },
    },
    "docs/ACCESSIBILITY_CONFORMANCE_REPORT.md": {
        "sources": set(),
        "markers": {
            "not a VPAT",
            "Current automated evidence",
            "28 production routes",
            "Manual NVDA protocol",
            "No WCAG level",
        },
    },
    "docs/THIRD_PARTY_SOFTWARE_INDEX.md": {
        "sources": {"docs/SLSA_LEVEL_3_ATTESTATION.md"},
        "markers": {
            "Dependency authorities",
            "SBOM and inventory set",
            "81 direct pins",
            "315 hash-locked packages",
            "alert 389",
            "Notice and redistribution approval gate",
        },
    },
    "docs/RELEASE_READINESS_RECORD.md": {
        "sources": {"docs/RELEASE_CHECKLIST.md"},
        "markers": {
            "**Production/public release: NO-GO.**",
            "Candidate identity",
            "5a76e0004e17ccee3e0721ec3f9fe0ee109ccc03d74c5ceb19273e99b3ae4620",
            "Gate summary",
            "Required final evidence bundle",
            "GO authorization template",
        },
    },
}
PROHIBITED_CLAIMS = {
    "production release is approved",
    "certified by microsoft",
    "fully compliant",
    "seaweedfs is the approved production object store",
}


def verify(authority: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    documents: list[dict[str, Any]] = []
    portal = (root / "docs" / "README.md").read_text(encoding="utf-8")
    routes = authority.get("merge_routes", {})

    for target, requirements in TARGETS.items():
        path = root / target
        item_errors: list[str] = []
        if not path.is_file():
            item_errors.append("missing_target")
            text = ""
            header: dict[str, str] = {}
        else:
            text = path.read_text(encoding="utf-8")
            header = parse_controlled_header(path)
        missing_markers = sorted(
            marker for marker in requirements["markers"] if marker not in text
        )
        item_errors.extend(f"missing_marker:{marker}" for marker in missing_markers)
        actual_sources = set(routes.get(target, []))
        if actual_sources != requirements["sources"]:
            item_errors.append("source_route_mismatch")
        if not header.get("Status"):
            item_errors.append("missing_controlled_status")
        if target not in portal:
            item_errors.append("documentation_portal_link_missing")
        lowered = text.casefold()
        item_errors.extend(
            f"prohibited_claim:{claim}"
            for claim in sorted(PROHIBITED_CLAIMS)
            if claim in lowered
        )
        errors.extend(f"{target}:{error}" for error in item_errors)
        documents.append(
            {
                "path": target,
                "status": header.get("Status"),
                "sources": sorted(actual_sources),
                "missing_markers": missing_markers,
                "errors": item_errors,
            }
        )

    return {
        "schema_version": "dle.engineering-assurance-document-verification.v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "authority_version": authority["program_version"],
        "status": "pass" if not errors else "fail",
        "target_count": len(TARGETS),
        "verified_count": sum(not item["errors"] for item in documents),
        "archive_delete_authorized": authority.get("approval", {}).get(
            "archive_delete_authorized"
        ),
        "errors": sorted(errors),
        "documents": documents,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    result = verify(load_authority(args.config))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        f"Engineering/assurance documentation: {result['status']} "
        f"verified={result['verified_count']}/{result['target_count']} "
        f"errors={len(result['errors'])}"
    )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
