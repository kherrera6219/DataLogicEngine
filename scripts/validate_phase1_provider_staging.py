"""Validate Phase 1 provider-backed gateway and audit persistence.

This is intentionally a live-provider smoke test. It loads provider keys from
the local environment/.env, runs a Tier 2 gateway request, and verifies that the
response includes the canonical audit footer and that a TruthAuditEvent row is
written to SQLite.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


DEFAULT_QUERY = (
    "Summarize the compliance audit controls required before releasing a "
    "desktop AI application."
)


def _sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.resolve().as_posix()}"


def _write_report(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


async def _run(args: argparse.Namespace) -> int:
    load_dotenv(REPO_ROOT / ".env")

    db_path = (REPO_ROOT / args.database_path).resolve()
    if db_path.exists() and args.reset_database:
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    os.environ["IS_DESKTOP_APP"] = "true"
    os.environ["DATABASE_URL"] = _sqlite_url(db_path)

    provider = args.provider.lower()
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for --provider openai")
    if provider == "google" and not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
        raise RuntimeError("GOOGLE_API_KEY or GEMINI_API_KEY is required for --provider google")
    if provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is required for --provider anthropic")

    from app import create_app
    from backend.llm_gateway.gateway import GatewayRequest, LLMGateway
    from backend.llm_gateway.model_defaults import default_model_for_provider
    from extensions import db
    from models import TruthAuditEvent, User

    model = args.model or default_model_for_provider(provider)
    app = create_app(
        "testing",
        config_overrides={
            "SQLALCHEMY_DATABASE_URI": os.environ["DATABASE_URL"],
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,
        },
    )

    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "database_url": os.environ["DATABASE_URL"],
        "desktop_mode": os.environ["IS_DESKTOP_APP"],
        "provider": provider,
        "model": model,
        "query_sha256": hashlib.sha256(args.query.encode("utf-8")).hexdigest(),
        "ok": False,
    }

    with app.app_context():
        db.create_all()
        if args.user_id is not None and not db.session.get(User, args.user_id):
            db.session.add(
                User(
                    id=args.user_id,
                    username=f"phase1-staging-{args.user_id}",
                    _email=f"phase1-staging-{args.user_id}@local.invalid",
                    active=True,
                )
            )
            db.session.commit()

        before = db.session.query(TruthAuditEvent).count()

        response = await LLMGateway(db.session).process(
            GatewayRequest(
                messages=[{"role": "user", "content": args.query}],
                provider=provider,
                model=model,
                run_ukg_pipeline=True,
                temperature=0.2,
                max_tokens=args.max_tokens,
                user_id=args.user_id,
                meta={},
            )
        )

        after = db.session.query(TruthAuditEvent).count()
        latest = db.session.query(TruthAuditEvent).order_by(TruthAuditEvent.id.desc()).first()
        footer_present = "[UKG Audit Trace]" in (response.content or "")
        tier = str(response.tier or "")
        audit_row_created = after > before
        latest_event_data = latest.event_data if latest else {}
        dsqp_chain = latest_event_data.get("dsqp_chain") if isinstance(latest_event_data, dict) else None
        dsqp_profiles = {}
        if isinstance(dsqp_chain, dict):
            for stage_payload in dsqp_chain.values():
                if isinstance(stage_payload, dict):
                    dsqp_profiles.update(stage_payload.get("profiles") or {})

        report.update(
            {
                "ok": bool(response.ok),
                "run_id": response.run_id,
                "provider_used": response.provider_used,
                "model_used": response.model_used,
                "tier": tier,
                "audit_footer_present": footer_present,
                "truth_audit_events_before": before,
                "truth_audit_events_after": after,
                "truth_audit_event_created": audit_row_created,
                "dsqp_chain_present": bool(dsqp_chain),
                "dsqp_profile_axes": sorted(dsqp_profiles),
                "latest_truth_audit_event": latest.to_dict() if latest else None,
                "usage": response.usage,
                "warnings": response.warnings,
                "error": response.error,
            }
        )

    _write_report(REPO_ROOT / args.report_path, report)

    failures: list[str] = []
    if not report["ok"]:
        failures.append(f"gateway response failed: {report.get('error')}")
    if tier != "T2":
        failures.append(f"expected Tier 2 response, got {tier or 'empty'}")
    if not footer_present:
        failures.append("missing [UKG Audit Trace] footer")
    if not audit_row_created:
        failures.append("TruthAuditEvent row was not created")
    if args.require_dsqp_chain and not report.get("dsqp_chain_present"):
        failures.append("TruthAuditEvent row does not include dsqp_chain")

    if failures:
        print("Phase 1 provider staging validation failed:")
        for failure in failures:
            print(f"- {failure}")
        print(f"Report: {args.report_path}")
        return 1

    print("Phase 1 provider staging validation passed")
    print(f"Provider/model: {report['provider_used']} / {report['model_used']}")
    print(f"Tier: {tier}")
    print(f"TruthAuditEvent rows: {before} -> {after}")
    if args.require_dsqp_chain:
        print(f"DSQP profile axes: {', '.join(report['dsqp_profile_axes'])}")
    print(f"Report: {args.report_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", default="openai", choices=["openai", "google", "anthropic"])
    parser.add_argument("--model", default=None)
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--user-id", type=int, default=1)
    parser.add_argument("--database-path", default="reports/phase1_provider_staging.sqlite")
    parser.add_argument("--report-path", default="reports/phase1_provider_staging_report.json")
    parser.add_argument("--reset-database", action="store_true")
    parser.add_argument("--require-dsqp-chain", action="store_true")
    args = parser.parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
