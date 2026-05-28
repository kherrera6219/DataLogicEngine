"""TruthMemoryCommitService — seals a completed TraceRun into the audit hash-chain.

On every Tier 2+ run completion this service:
  1. Serialises the TraceRun and all linked evidence/personas/KA invocations
  2. Computes evidence_pack_hash (SHA-256 of the canonical JSON bundle)
  3. Writes a TruthAuditEvent via AuditLogger (adds the hash-chain link)
  4. Stores evidence_pack_hash back on the TraceRun row
  5. Returns the hash_chain value as a verifiable receipt token
"""

import hashlib
import asyncio
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
            object_ref = self._write_audit_bundle_object(run, bundle)
            merkle_root = self._create_merkle_root(bundle)
            anchor = self._anchor_merkle_root(run, merkle_root) if self._requires_blockchain_anchor(run) else None

            receipt = self._write_audit_event(
                run,
                db_session,
                bundle,
                evidence_pack_hash,
                object_ref=object_ref,
                merkle_root=merkle_root,
                anchor=anchor,
            )

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
    def _write_audit_bundle_object(run, bundle: dict) -> dict:
        """Persist canonical audit bundle JSON to the app-owned object store."""
        bucket = "audit_logs"
        key = f"{run.run_id}.json"
        try:
            from backend.storage import get_object_store

            payload = json.dumps(bundle, sort_keys=True, default=str, indent=2).encode("utf-8")
            store = get_object_store()
            store.create_bucket(bucket)
            store.put(
                bucket,
                key,
                payload,
                content_type="application/json",
                metadata={
                    "run_id": str(run.run_id),
                    "tier": str(getattr(run, "tier", "") or ""),
                    "evidence_pack_hash": TruthMemoryCommitService._hash_bundle(bundle),
                },
            )
            return {"bucket": bucket, "key": key}
        except Exception as exc:
            logger.warning("Audit bundle object-store write skipped for run %s: %s", run.run_id, exc)
            return {}

    @staticmethod
    def _create_merkle_root(bundle: dict) -> str:
        try:
            from backend.truth_engine.truth_link.blockchain_adapter import MerkleTree

            blocks = [
                json.dumps({"section": section, "data": value}, sort_keys=True, default=str)
                for section, value in sorted(bundle.items())
            ]
            return MerkleTree(blocks).get_root()
        except Exception:
            return TruthMemoryCommitService._hash_bundle(bundle)

    @staticmethod
    def _requires_blockchain_anchor(run) -> bool:
        tier = str(getattr(run, "tier", "") or "").lower()
        if tier in {"3", "t3", "tier_3", "tier3", "high_stakes", "extreme", "autonomous"}:
            return True
        try:
            return int(tier) >= 3
        except ValueError:
            return False

    @staticmethod
    def _anchor_merkle_root(run, merkle_root: str) -> dict:
        try:
            from backend.truth_engine.truth_link.blockchain_adapter import blockchain_adapter

            metadata = {
                "run_id": str(run.run_id),
                "tier": getattr(run, "tier", None),
                "status": getattr(run, "status", None),
            }
            return asyncio.run(blockchain_adapter.anchor_to_blockchain(merkle_root, metadata))
        except RuntimeError:
            try:
                from backend.truth_engine.truth_link.blockchain_adapter import blockchain_adapter

                return blockchain_adapter._simulated_anchor(  # pylint: disable=protected-access
                    merkle_root,
                    {"run_id": str(run.run_id), "tier": getattr(run, "tier", None)},
                )
            except Exception as exc:
                return {"error": str(exc), "merkle_root": merkle_root}
        except Exception as exc:
            return {"error": str(exc), "merkle_root": merkle_root}

    @staticmethod
    def _write_audit_event(
        run,
        db_session,
        bundle: dict,
        evidence_pack_hash: str,
        object_ref: Optional[dict] = None,
        merkle_root: Optional[str] = None,
        anchor: Optional[dict] = None,
    ) -> str:
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
        object_ref = object_ref or {}
        if object_ref:
            event_data["object_store"] = object_ref
        if merkle_root:
            event_data["merkle_root"] = merkle_root
        if anchor:
            event_data["blockchain_anchor"] = anchor
        dsqp_chain = TruthMemoryCommitService._extract_dsqp_chain(run, bundle)
        if dsqp_chain:
            event_data["dsqp_chain"] = dsqp_chain
        record = audit.log_event(
            session_id=session_id,
            event_type="audit_bundle_commit",
            event_data=event_data,
            category="audit",
        )
        TruthMemoryCommitService._update_audit_artifact_fields(
            db_session,
            record.get("event_id"),
            object_ref=object_ref,
            merkle_root=merkle_root,
            anchor=anchor,
        )
        return record.get("hash_chain", "")

    @staticmethod
    def _update_audit_artifact_fields(
        db_session,
        event_id: Optional[str],
        object_ref: Optional[dict] = None,
        merkle_root: Optional[str] = None,
        anchor: Optional[dict] = None,
    ) -> None:
        if not event_id:
            return
        try:
            from models import TruthAuditEvent

            event = db_session.query(TruthAuditEvent).filter_by(event_id=event_id).first()
            if not event:
                return
            object_ref = object_ref or {}
            anchor = anchor or {}
            event.object_store_bucket = object_ref.get("bucket")
            event.object_store_key = object_ref.get("key")
            event.merkle_root = merkle_root
            event.blockchain_anchor_tx = anchor.get("transaction_hash")
            event.blockchain_anchor_status = "error" if anchor.get("error") else ("anchored" if anchor else None)
            db_session.add(event)
            db_session.commit()
        except Exception as exc:
            logger.warning("Audit artifact field update skipped for event %s: %s", event_id, exc)
            try:
                db_session.rollback()
            except Exception:
                pass

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
