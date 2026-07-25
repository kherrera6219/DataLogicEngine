#!/usr/bin/env python3
"""Generate the reproducible Phase 0 acceptance and feature ledgers."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / "reports/production-readiness/2026/phase-00"
RUNTIME = PHASE / "runtime"


def load(name: str) -> dict[str, Any]:
    return json.loads((RUNTIME / name).read_text(encoding="utf-8"))


def stable_id(prefix: str, value: object) -> str:
    digest = hashlib.sha256(
        json.dumps(value, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:12]
    return f"{prefix}-{digest}"


def requirement(
    identifier: str,
    intent: str,
    phase: int,
    ui: str,
    contract: str,
    owner: str,
    tests: list[str],
    evidence: str,
    docs: list[str],
) -> dict[str, Any]:
    return {
        "id": identifier,
        "product_intent": intent,
        "ui_surface": ui,
        "contract": contract,
        "owning_service_or_store": owner,
        "implementation": f"Phase {phase} work package",
        "automated_tests": tests,
        "manual_tests": [f"Phase {phase} installed-system acceptance"],
        "evidence": evidence,
        "user_documentation": docs,
        "target_phase": phase,
        "status": "finish",
        "acceptance_authority": "Kevin - DataLogicEngine owner",
    }


def requirements() -> list[dict[str, Any]]:
    return [
        requirement(
            "REQ-001",
            "Install and operate the signed Windows 11 x64 application",
            14,
            "Installer and desktop shell",
            "Installer lifecycle",
            "Desktop application",
            ["installer lifecycle suite"],
            "phase-14",
            ["docs/DEPLOYMENT.md"],
        ),
        requirement(
            "REQ-002",
            "Use the API gateway as the governed integration surface",
            8,
            "Gateway settings and diagnostics",
            "Versioned REST and streaming API",
            "Flask gateway",
            ["gateway contract suite"],
            "phase-08",
            ["docs/API_REFERENCE.md"],
        ),
        requirement(
            "REQ-003",
            "Use one causal governed reasoning path for desktop and external clients",
            5,
            "Built-in chat",
            "Canonical governed request lifecycle",
            "Reasoning runtime",
            ["causal lifecycle suite"],
            "phase-05",
            ["docs/ARCHITECTURE.md"],
        ),
        requirement(
            "REQ-004",
            "Persist relational application and audit state",
            4,
            "Administration and audit",
            "PostgreSQL data contract",
            "PostgreSQL",
            ["migration and persistence suite"],
            "phase-04",
            ["docs/DATABASE_SCHEMA.md"],
        ),
        requirement(
            "REQ-005",
            "Provide durable queue, cache, idempotency, and event behavior",
            3,
            "Runtime health",
            "Redis service contract",
            "Redis",
            ["service parity suite"],
            "phase-03",
            ["docs/DEPLOYMENT.md"],
        ),
        requirement(
            "REQ-006",
            "Provide durable graph relationships and provenance traversal",
            9,
            "Graph workspace",
            "Neo4j graph contract",
            "Neo4j",
            ["graph causality suite"],
            "phase-09",
            ["docs/DATABASE_SCHEMA.md"],
        ),
        requirement(
            "REQ-007",
            "Provide local semantic retrieval",
            9,
            "Knowledge workspace",
            "Chroma collection contract",
            "ChromaDB",
            ["retrieval suite"],
            "phase-09",
            ["docs/DATABASE_SCHEMA.md"],
        ),
        requirement(
            "REQ-008",
            "Store and recover object artifacts with integrity metadata",
            4,
            "Exports and diagnostics",
            "S3-compatible object contract",
            "App-owned S3-compatible object store",
            ["backup restore suite"],
            "phase-04",
            ["docs/DEPLOYMENT.md"],
        ),
        requirement(
            "REQ-009",
            "Protect mutations, IPC, MCP, and file operations",
            1,
            "All privileged controls",
            "Authorization and capability policy",
            "Security boundary",
            ["authorization matrix suite"],
            "phase-01",
            ["docs/SECURITY.md"],
        ),
        requirement(
            "REQ-010",
            "Return typed safe public errors",
            1,
            "All user-facing workflows",
            "Public error envelope",
            "Gateway and desktop",
            ["error contract suite"],
            "phase-01",
            ["docs/API_REFERENCE.md"],
        ),
        requirement(
            "REQ-011",
            "Report required-service capability truthfully without silent fallback",
            2,
            "Health and diagnostics",
            "Capability-state contract",
            "Runtime factory",
            ["capability state suite"],
            "phase-02",
            ["docs/ARCHITECTURE.md"],
        ),
        requirement(
            "REQ-012",
            "Execute only supported OpenAI and Google provider branches",
            7,
            "Provider settings",
            "Provider adapter contract",
            "Provider runtime",
            ["provider contract suite"],
            "phase-07",
            ["docs/PROVIDER_SETUP_GUIDE.md"],
        ),
        requirement(
            "REQ-013",
            "Record causal evidence, confidence, convergence, and TruthCore outputs",
            6,
            "Runs and Truth Engine",
            "Evidence and trace schema",
            "Truth runtime",
            ["evidence validity suite"],
            "phase-06",
            ["docs/ARCHITECTURE.md"],
        ),
        requirement(
            "REQ-014",
            "Ingest, retrieve, graph, and remember data with source identity",
            9,
            "Knowledge and graph",
            "Ingestion and retrieval contracts",
            "Knowledge runtime",
            ["knowledge lifecycle suite"],
            "phase-09",
            ["docs/USER_GUIDE.md"],
        ),
        requirement(
            "REQ-015",
            "Run only completed and truthfully labeled simulations",
            10,
            "Simulations",
            "Simulation contract",
            "Simulation runtime",
            ["simulation suite"],
            "phase-10",
            ["docs/USER_GUIDE.md"],
        ),
        requirement(
            "REQ-016",
            "Operate approved MCP servers and connectors within explicit scopes",
            11,
            "MCP administration",
            "MCP protocol and scope contract",
            "MCP runtime",
            ["MCP conformance suite"],
            "phase-11",
            ["docs/MCP_USER_GUIDE.md"],
        ),
        requirement(
            "REQ-017",
            "Make every enabled desktop control perform its stated real-backend action",
            12,
            "All desktop pages",
            "Preload and backend contracts",
            "Electron and frontend",
            ["UI workflow suite"],
            "phase-12",
            ["docs/USER_GUIDE.md"],
        ),
        requirement(
            "REQ-018",
            "Provide redacted diagnostics, audit, and support evidence",
            13,
            "Diagnostics and audit",
            "Observability and support bundle",
            "Observability runtime",
            ["diagnostic redaction suite"],
            "phase-13",
            ["docs/OPERATIONS.md"],
        ),
        requirement(
            "REQ-019",
            "Build reproducible, signed, update-verifiable artifacts",
            14,
            "Installer and updater",
            "Release and update contract",
            "Release pipeline",
            ["supply-chain suite"],
            "phase-14",
            ["docs/RELEASE_READINESS_RECORD.md"],
        ),
        requirement(
            "REQ-020",
            "Prove clean-install, upgrade, recovery, performance, security, and human acceptance",
            15,
            "Complete product",
            "System acceptance contract",
            "Installed system",
            ["release-candidate qualification"],
            "phase-15",
            ["docs/PRODUCTION_READINESS.md"],
        ),
    ]


def target_for_route(route: dict[str, Any]) -> int:
    methods = set(route.get("methods", []))
    if methods & {"POST", "PUT", "PATCH", "DELETE"}:
        return 1
    if route.get("classification") == "client-gateway":
        return 8
    if route.get("classification") == "internal-service":
        return 2
    return 12


def feature_item(
    kind: str, source: object, phase: int, rationale: str
) -> dict[str, Any]:
    return {
        "id": stable_id(kind.upper().replace("_", "-"), source),
        "kind": kind,
        "source": source,
        "disposition": "finish",
        "rationale": rationale,
        "target_phase": phase,
        "owner": "Kevin - DataLogicEngine owner",
        "verification_status": "pending",
    }


def features() -> list[dict[str, Any]]:
    runtime = load("runtime-surfaces.json")
    ui = load("ui-controls.json")
    services = load("service-consumers.json")
    items: list[dict[str, Any]] = []
    for page in ui["pages"]:
        items.append(
            feature_item(
                "page",
                page,
                12,
                "Retain only after installed real-backend workflow acceptance.",
            )
        )
    for control in ui["controls"]:
        items.append(
            feature_item(
                "ui_control",
                control,
                12,
                "Verify behavior; disable or remove if the promised action is not completed.",
            )
        )
    for route in runtime["flask_routes"]:
        items.append(
            feature_item(
                "flask_route",
                route,
                target_for_route(route),
                "Classify and enforce its production contract before shipment.",
            )
        )
    for key, phase in (
        ("graphql_operations", 1),
        ("electron_ipc", 1),
        ("websocket_sse", 8),
        ("preload_exports", 1),
        ("mcp_methods", 11),
        ("local_file_entries", 1),
        ("external_network_domains", 7),
    ):
        for value in runtime.get(key, []):
            items.append(
                feature_item(
                    key.rstrip("s"),
                    value,
                    phase,
                    "Retain only with an explicit production boundary and test.",
                )
            )
    for service, consumers in services["service_consumers"].items():
        for consumer in consumers:
            items.append(
                feature_item(
                    f"{service}_consumer",
                    consumer,
                    3,
                    "Bind to the approved required-service contract.",
                )
            )
    for fallback in services["fallback_references"]:
        items.append(
            feature_item(
                "fallback",
                fallback,
                3,
                "Prove non-production use or disable/remove silent production fallback.",
            )
        )
    return items


def write_json(name: str, payload: dict[str, Any]) -> None:
    (PHASE / name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    generated_at = datetime.now(UTC).isoformat()
    reqs = requirements()
    feature_rows = features()
    write_json(
        "requirements-traceability.json",
        {
            "schema_version": "1.0.0",
            "generated_at": generated_at,
            "status": "phase targets assigned; acceptance evidence pending",
            "requirements": reqs,
        },
    )
    write_json(
        "feature-disposition.json",
        {
            "schema_version": "1.0.0",
            "generated_at": generated_at,
            "status": "all inventoried items assigned; behavior verification pending",
            "allowed_dispositions": ["ship", "finish", "disable", "defer", "remove"],
            "features": feature_rows,
            "summary": {
                "total": len(feature_rows),
                "finish": sum(row["disposition"] == "finish" for row in feature_rows),
            },
        },
    )
    print(
        f"Wrote {len(reqs)} requirements and {len(feature_rows)} feature dispositions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
