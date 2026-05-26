"""TruthMemoryCommitService — seals a completed TraceRun into the audit hash-chain.

On every Tier 2+ run completion this service:
  1. Serialises the TraceRun and all linked evidence/personas/KA invocations
  2. Computes evidence_pack_hash (SHA-256 of the canonical JSON bundle)
  3. Writes a TruthAuditEvent via AuditLogger (adds the hash-chain link)
  4. Stores evidence_pack_hash back on the TraceRun row
  5. Returns the hash_chain value as a verifiable receipt token
"""

import hashlib
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TruthMemoryCommitService:

    def commit(self, run, db_session) -> Optional[str]:
        """
        Seal a completed TraceRun into the audit chain.

        Parameters
        ----------
        run : TraceRun
            A fully-populated TraceRun ORM object (with linked relationships loaded).
        db_session :
            Active SQLAlchemy session to use for writes.

        Returns
        -------
        str or None
            The hash_chain receipt token, or None if the commit failed.
        """
        try:
            bundle = self._build_bundle(run, db_session)
            evidence_pack_hash = self._hash_bundle(bundle)

            receipt = self._write_audit_event(run, db_session, bundle, evidence_pack_hash)

            run.evidence_pack_hash = evidence_pack_hash
            db_session.add(run)
            db_session.commit()

            logger.info(
                "TruthMemory commit: run=%s tier=%s hash=%s...",
                run.run_id,
                run.tier,
                evidence_pack_hash[:16],
            )
            return receipt

        except Exception as exc:
            logger.error("TruthMemory commit failed for run %s: %s", run.run_id, exc)
            try:
                db_session.rollback()
            except Exception:
                pass
            return None

    def _build_bundle(self, run, db_session) -> dict:
        """Serialise the TraceRun and linked rows into the canonical AuditBundle dict."""
        evidence = [e.to_dict() for e in run.evidence_items] if run.evidence_items else []
        personas = [p.to_dict() for p in run.personas] if run.personas else []
        ka_invocations = [k.to_dict() for k in run.ka_invocations] if run.ka_invocations else []
        stages = [s.to_dict() for s in run.stages] if run.stages else []

        return {
            "run_id": str(run.run_id),
            "tier": run.tier,
            "status": run.status,
            "input_message": run.input_message,
            "final_answer": run.final_answer,
            "confidence": run.confidence,
            "layers_executed": run.layers_executed,
            "refinement_cycles": run.refinement_cycles,
            "regulatory_pass": run.regulatory_pass,
            "security_pass": run.security_pass,
            "truthgate_decision": run.truthgate_decision,
            "token_cost": run.token_cost,
            "latency_ms": run.latency_ms,
            "model_name": run.model_name,
            "evidence": evidence,
            "personas": personas,
            "ka_invocations": ka_invocations,
            "stages": stages,
        }

    @staticmethod
    def _hash_bundle(bundle: dict) -> str:
        canonical = json.dumps(bundle, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    @staticmethod
    def _write_audit_event(run, db_session, bundle: dict, evidence_pack_hash: str) -> str:
        from backend.truth_engine.truth_memory.audit import AuditLogger

        audit = AuditLogger(db_session=db_session)
        session_id = None  # truth_audit_events.session_id FK → truth_sessions; no truth session in this flow
        event_data = {
            "evidence_pack_hash": evidence_pack_hash,
            "tier": run.tier,
            "status": run.status,
            "confidence": run.confidence,
            "truthgate_decision": run.truthgate_decision,
        }
        dsqp_chain = TruthMemoryCommitService._extract_dsqp_chain(run, bundle)
        if dsqp_chain:
            event_data["dsqp_chain"] = dsqp_chain
        record = audit.log_event(
            session_id=session_id,
            event_type="audit_bundle_commit",
            event_data=event_data,
            category="audit",
        )
        return record.get("hash_chain", "")

    @staticmethod
    def _extract_dsqp_chain(run, bundle: dict) -> dict:
        explicit = getattr(run, "dsqp_chain", None)
        if explicit:
            return explicit
        chains = {}
        for stage in bundle.get("stages", []) or []:
            outputs = stage.get("outputs") or {}
            if not isinstance(outputs, dict):
                continue
            if outputs.get("dsqp_chain"):
                chains[stage.get("name") or "stage"] = outputs["dsqp_chain"]
            for axis, profile in (outputs.get("constructed_persona_profiles") or {}).items():
                metadata = profile.get("metadata", {}) if isinstance(profile, dict) else {}
                if metadata.get("dsqp_chain"):
                    chains[str(axis)] = metadata["dsqp_chain"]
        return chains
