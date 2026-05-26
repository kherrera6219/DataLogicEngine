"""Validate Phase F DMRF desktop/VM-compatible control-plane evidence."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.resolve().as_posix()}"


async def _run_one(database_url: str, label: str, *, desktop_mode: bool, offline: bool) -> dict:
    from app import create_app
    from backend.dmrf import DMRFOrchestrator
    from extensions import db
    from models import TruthAuditEvent

    app = create_app(
        "testing",
        config_overrides={
            "SQLALCHEMY_DATABASE_URI": database_url,
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,
        },
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
        before = TruthAuditEvent.query.count()
        start = time.perf_counter()
        result = await DMRFOrchestrator(
            desktop_mode=desktop_mode,
            db_session=db.session,
        ).process(
            "Assess finance compliance audit controls for a release gate",
            context={"risk_domain": "finance"},
            offline=offline,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        after = TruthAuditEvent.query.count()
        row = TruthAuditEvent.query.filter_by(event_type="dmrf_result").order_by(TruthAuditEvent.id.desc()).first()
        return {
            "label": label,
            "ok": result.ok,
            "tier": result.tier,
            "axis_count": len(result.axis_vector.axes) if result.axis_vector else 0,
            "frost_depth": result.axis_vector.frost_layer_depth if result.axis_vector else 0,
            "step_count": len(result.steps),
            "elapsed_ms": round(elapsed_ms, 3),
            "audit_rows_before": before,
            "audit_rows_after": after,
            "audit_persisted": row is not None and row.event_data.get("run_id") == result.run_id,
            "dsqp_profiles": sorted((result.dsqp_chain.get("profiles") or {}).keys()),
            "warnings": result.warnings,
        }


async def _run(args: argparse.Namespace) -> int:
    sqlite_path = REPO_ROOT / args.sqlite_path
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    if sqlite_path.exists() and args.reset:
        sqlite_path.unlink()

    internal_url = _sqlite_url(sqlite_path)
    checks = [
        await _run_one(internal_url, "desktop_windows_internal", desktop_mode=True, offline=True),
        await _run_one(internal_url, "vm_windows_internal", desktop_mode=False, offline=False),
    ]

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "phase": "F",
        "environment_model": "desktop and VM both run the same Windows application with bundled/internal databases; no external database source is required or expected",
        "checks": checks,
        "rust_f2_decision": {
            "required": False,
            "reason": "F2 is optional unless profiling shows a Python bottleneck; current Phase F evidence validates the Python control plane on the same internal database model used for desktop and Windows VM.",
        },
    }
    report_path = REPO_ROOT / args.report_path
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    failures = [
        check
        for check in checks
        if not check.get("ok")
        or (not check.get("skipped") and not check.get("audit_persisted", False))
        or (not check.get("skipped") and check.get("axis_count") != 17)
    ]
    if failures:
        print("DMRF Phase F validation failed")
        print(f"Report: {args.report_path}")
        return 1

    print("DMRF Phase F validation passed")
    print(f"Report: {args.report_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sqlite-path", default="reports/dmrf_phase_f.sqlite")
    parser.add_argument("--report-path", default="reports/dmrf_phase_f_validation.json")
    parser.add_argument("--reset", action="store_true")
    return asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
