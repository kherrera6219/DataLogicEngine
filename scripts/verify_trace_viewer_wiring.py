"""Generate local Trace Viewer wiring evidence with a disposable database."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import uuid


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    report_path = root / "reports" / "trace_viewer_wiring_evidence.json"

    with tempfile.TemporaryDirectory(prefix="dle_trace_viewer_") as tmp:
        db_path = Path(tmp) / "trace.sqlite3"

        import app as app_module
        from backend.llm_gateway.api import _audit_trail_for_run
        from backend.tracing.api import _build_trace_bundle
        from extensions import db
        from models import TraceEvidence, TraceKAInvocation, TracePersona, TraceRun, TraceStage

        app_module.app.config["TESTING"] = True
        app_module.app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path.as_posix()}"

        run_id = uuid.uuid4()
        with app_module.app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()
            run = TraceRun(
                run_id=run_id,
                status="running",
                input_message="Trace viewer evidence query",
                final_answer="Trace viewer evidence answer",
                confidence=0.93,
                tier="2",
            )
            db.session.add(run)
            db.session.add(
                TraceStage(
                    run_id=run_id,
                    name="L1 Context",
                    stage_type="layer",
                    layer_index=1,
                    status="completed",
                    duration_ms=10,
                    metrics={"tokens_in": 3, "tokens_out": 7, "retrieval_count": 1},
                )
            )
            db.session.add(
                TraceEvidence(
                    run_id=run_id,
                    source_type="knowledge_graph",
                    source_id="kg-fixture",
                    source_title="Trace Fixture",
                    authority="high",
                    retrieval_method="ka-018",
                    relevance_score=0.9,
                    used_by_claims=["claim-1"],
                    used_by_stages=["L2"],
                )
            )
            db.session.add(
                TracePersona(
                    run_id=run_id,
                    persona_type="knowledge",
                    persona_name="Knowledge Expert",
                    status="pass",
                    draft_text="Persona trace position",
                    confidence=0.84,
                    consensus_impact={"synthesis_weight": 0.4},
                )
            )
            db.session.add(
                TraceKAInvocation(
                    run_id=run_id,
                    ka_id="KA-018",
                    ka_name="Source Provenance",
                    status="completed",
                    duration_ms=5,
                )
            )
            db.session.commit()

            bundle = _build_trace_bundle(run)
            db.session.remove()

        audit_trail = _audit_trail_for_run(str(run_id))
        evidence = {
            "success": (
                audit_trail is not None
                and audit_trail["complete_trace_url"].endswith(f"/{run_id}/bundle")
                and bundle["run_id"] == str(run_id)
                and bundle["metrics"]["stage_count"] == 1
                and bundle["evidence_sources"][0]["evidence_tier"] == "GOLD"
                and bundle["personas"][0]["synthesis_weight"] == 0.4
                and bundle["ka_invocations"][0]["ka_id"] == "KA-018"
            ),
            "audit_trail": audit_trail,
            "bundle_keys": sorted(bundle.keys()),
            "stage_count": bundle["metrics"]["stage_count"],
            "evidence_tier": bundle["evidence_sources"][0]["evidence_tier"],
            "persona_count": len(bundle["personas"]),
            "ka_count": len(bundle["ka_invocations"]),
        }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps({"success": evidence["success"], "report": str(report_path)}, indent=2))
    return 0 if evidence["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
