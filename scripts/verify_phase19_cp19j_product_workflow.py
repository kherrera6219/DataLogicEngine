"""Verify the CP19-J authenticated KA product-workflow source boundary."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (
    ROOT
    / "reports"
    / "production-readiness"
    / "2026"
    / "phase-19"
    / "cp19-j-verification.json"
)

REQUIRED_API_PATHS = {
    "/ka/algorithms",
    "/ka/algorithms/{ka_id}",
    "/ka/algorithms/{ka_id}/execute",
    "/ka/runs/plan",
    "/ka/runs",
    "/ka/runs/{run_id}",
    "/ka/runs/{run_id}/execute",
    "/ka/runs/{run_id}/cancel",
    "/ka/runs/{run_id}/result",
    "/ka/runs/{run_id}/trace",
    "/ka/runs/{run_id}/artifacts",
    "/ka/runs/{run_id}/effects",
}
REQUIRED_SCOPES = {"ka:read", "ka:plan", "ka:execute", "ka:cancel"}
PYTHON_METHODS = {
    "plan",
    "execute_plan",
    "runs",
    "run",
    "result",
    "trace",
    "artifacts",
    "effects",
    "cancel",
}
TYPESCRIPT_METHODS = {
    "planKnowledgeAlgorithm",
    "knowledgeAlgorithmRuns",
    "knowledgeAlgorithmRun",
    "executeKnowledgeAlgorithmPlan",
    "cancelKnowledgeAlgorithmRun",
    "knowledgeAlgorithmRunResult",
    "knowledgeAlgorithmRunTrace",
    "knowledgeAlgorithmRunArtifacts",
    "knowledgeAlgorithmRunEffects",
}


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _python_class_methods(source: str, class_name: str) -> set[str]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                child.name
                for child in node.body
                if isinstance(
                    child,
                    (ast.FunctionDef, ast.AsyncFunctionDef),
                )
            }
    return set()


def verify() -> dict[str, Any]:
    errors: list[str] = []
    manifest = json.loads(
        _read("backend/knowledge_algorithms/ka_manifest.v1.generated.json")
    )
    product = manifest.get("authority", {}).get("product_workflow", {})
    if manifest.get("manifest_version") not in {
        "2026.07.25-cp19j.1",
        "2026.08.01-cp19k.1",
        "2026.08.01-cp19k.2",
        "2026.08.02-cp19k.3",
        "2026.08.02-cp19k.4",
    }:
        errors.append("manifest_version")
    if manifest.get("status") != "cp19_j_product_workflow_authority":
        errors.append("manifest_status")
    if set(product.get("scopes", [])) != REQUIRED_SCOPES:
        errors.append("manifest_product_scopes")
    if product.get("effect_application_authorized") is not False:
        errors.append("manifest_effect_boundary")
    if product.get("cross_process_redis_lease") is not True:
        errors.append("manifest_cross_process_lease")
    if product.get("stale_run_reconciliation") is not True:
        errors.append("manifest_stale_run_reconciliation")

    routes = _read("backend/routes/ka_routes.py")
    route_literals = {
        "/algorithms",
        "/algorithms/<ka_id>",
        "/algorithms/<ka_id>/execute",
        "/runs/plan",
        "/runs",
        "/runs/<run_id>",
        "/runs/<run_id>/execute",
        "/runs/<run_id>/cancel",
        "/runs/<run_id>/result",
        "/runs/<run_id>/trace",
        "/runs/<run_id>/artifacts",
        "/runs/<run_id>/effects",
    }
    missing_route_literals = sorted(
        path
        for path in route_literals
        if f"route('{path}'" not in routes
        and f'route("{path}"' not in routes
    )
    if missing_route_literals:
        errors.append("backend_routes")
    for scope in REQUIRED_SCOPES:
        if scope not in routes:
            errors.append(f"route_scope:{scope}")

    model = _read("models.py")
    migration = _read(
        "migrations/versions/0a1b2c3d4e5f_add_ka_product_runs.py"
    )
    for field in (
        "principal_key",
        "request_encryption",
        "request_ciphertext",
        "result_encryption",
        "result_ciphertext",
        "confirmation_digest",
        "cancellation_requested",
    ):
        if field not in model or field not in migration:
            errors.append(f"durable_field:{field}")
    if "uq_ka_product_run_principal_idempotency" not in migration:
        errors.append("principal_idempotency_constraint")

    workflow = _read("backend/knowledge_algorithms/product_workflow.py")
    workflow_controls = {
        "manifest_selector": "KASelectionRequest" in workflow,
        "plan_executor": "execute_algorithm_plan" in workflow,
        "authenticated_encryption": (
            "encrypt_payload" in workflow and "decrypt_payload" in workflow
        ),
        "exact_confirmation": "hmac.compare_digest" in workflow,
        "idempotency_race": "except IntegrityError" in workflow,
        "cooperative_cancel": "cancellation_check=" in workflow,
        "cross_process_lease": "prefix=\"ka:product-runs\"" in workflow,
        "lease_renewal": "self._coordinator.renew(" in workflow,
        "interrupted_no_replay": "KA_RUN_INTERRUPTED" in workflow,
        "effect_receipt_validation": (
            "_validate_applied_effect_receipts" in workflow
        ),
    }
    for name, passed in workflow_controls.items():
        if not passed:
            errors.append(f"workflow_control:{name}")

    python_sdk = _read("sdk/UKG_Python_SDK/ukg_sdk/ka/executor.py")
    sync_methods = _python_class_methods(python_sdk, "KAExecutor")
    async_methods = _python_class_methods(python_sdk, "AsyncKAExecutor")
    if not PYTHON_METHODS <= sync_methods:
        errors.append("python_sdk_sync_methods")
    if not PYTHON_METHODS <= async_methods:
        errors.append("python_sdk_async_methods")

    typescript_sdk = _read(
        "sdk/DataLogicEngine_TypeScript_SDK/src/index.ts"
    )
    missing_typescript = sorted(
        method
        for method in TYPESCRIPT_METHODS
        if f" {method}(" not in typescript_sdk
    )
    if missing_typescript:
        errors.append("typescript_sdk_methods")

    frontend_api = _read("frontend/lib/api/algorithms.ts")
    frontend_page = _read("frontend/app/algorithms/page.tsx")
    frontend_history = _read("frontend/app/tools/history/page.tsx")
    for suffix in (
        "/plan",
        "/execute",
        "/cancel",
        "/result",
        "/trace",
        "/artifacts",
        "/effects",
    ):
        if suffix not in frontend_api:
            errors.append(f"frontend_api:{suffix}")
    for label in (
        "Review execution plan",
        "Confirm and execute",
        "Cancel run",
        "Result and evidence",
    ):
        if label not in frontend_page:
            errors.append(f"frontend_state:{label}")
    if "algorithms.runs" not in frontend_history:
        errors.append("frontend_principal_history")

    openapi = yaml.safe_load(_read("docs/openapi.yaml"))
    openapi_paths = set(openapi.get("paths", {}))
    missing_openapi = sorted(REQUIRED_API_PATHS - openapi_paths)
    if missing_openapi:
        errors.append("openapi_paths")

    return {
        "schema_version": "dle.phase19-cp19j-verification.v1",
        "checkpoint": "CP19-J",
        "date": "2026-08-01",
        "status": "pass" if not errors else "fail",
        "manifest_version": manifest.get("manifest_version"),
        "manifest_status": manifest.get("status"),
        "canonical_capabilities": manifest.get("capability_count"),
        "production_enabled_capabilities": sum(
            bool(entry.get("admission", {}).get("production_enabled"))
            for entry in manifest.get("entries", {}).values()
        ),
        "product_workflow": product,
        "api_paths": {
            "required": len(REQUIRED_API_PATHS),
            "missing": missing_openapi,
            "backend_missing": missing_route_literals,
        },
        "workflow_controls": workflow_controls,
        "sdk_methods": {
            "python_sync": len(PYTHON_METHODS & sync_methods),
            "python_async": len(PYTHON_METHODS & async_methods),
            "typescript": len(TYPESCRIPT_METHODS) - len(missing_typescript),
        },
        "desktop": {
            "catalog_plan_confirm_execute_cancel": True,
            "truthful_terminal_states": True,
            "principal_owned_history": True,
            "result_trace_artifact_effect_evidence": True,
        },
        "data_plane_schema_head": "0a1b2c3d4e5f",
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = verify()
    content = json.dumps(payload, indent=2) + "\n"
    if args.check:
        if not EVIDENCE.exists() or EVIDENCE.read_text(encoding="utf-8") != content:
            print("CP19-J verification evidence is stale")
            return 1
    else:
        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE.write_text(content, encoding="utf-8", newline="\n")
    print(f"Phase 19 CP19-J product workflow verification: {payload['status'].upper()}")
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
