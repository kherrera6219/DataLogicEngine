"""W3C PROV-JSON records for TruthMemory audit events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import hashlib
from typing import Any


@dataclass
class ProvenanceRecord:
    """SQLite-serialisable W3C PROV-JSON record."""

    entity_id: str
    activity_id: str
    agent_id: str = "DataLogicEngine.TruthMemory"
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    attributes: dict[str, Any] = field(default_factory=dict)
    used_entities: list[str] = field(default_factory=list)

    @classmethod
    def from_trace_run(cls, run: Any, *, evidence_pack_hash: str, object_ref: dict[str, Any] | None = None) -> "ProvenanceRecord":
        run_id = str(getattr(run, "run_id", "unknown"))
        return cls(
            entity_id=f"trace_run:{run_id}",
            activity_id=f"audit_bundle_commit:{run_id}",
            attributes={
                "prov:type": "dle:AuditBundle",
                "dle:run_id": run_id,
                "dle:tier": getattr(run, "tier", None),
                "dle:status": getattr(run, "status", None),
                "dle:evidence_pack_hash": evidence_pack_hash,
                "dle:object_store": object_ref or {},
            },
            used_entities=[f"trace_run_input:{run_id}", f"trace_run_evidence:{evidence_pack_hash[:16]}"],
        )

    def to_w3c_prov(self) -> dict[str, Any]:
        entity = {
            self.entity_id: {
                "prov:label": self.entity_id,
                "prov:generatedAtTime": self.generated_at,
                **self.attributes,
            }
        }
        activity = {
            self.activity_id: {
                "prov:label": self.activity_id,
                "prov:startTime": self.generated_at,
                "prov:endTime": self.generated_at,
            }
        }
        agent = {
            self.agent_id: {
                "prov:type": "prov:SoftwareAgent",
                "prov:label": self.agent_id,
            }
        }
        used = {
            f"{self.activity_id}:used:{index}": {
                "prov:activity": self.activity_id,
                "prov:entity": entity_id,
            }
            for index, entity_id in enumerate(self.used_entities)
        }
        return {
            "prefix": {
                "prov": "http://www.w3.org/ns/prov#",
                "dle": "https://datalogicengine.local/prov#",
            },
            "entity": entity,
            "activity": activity,
            "agent": agent,
            "wasGeneratedBy": {
                f"{self.entity_id}:generation": {
                    "prov:entity": self.entity_id,
                    "prov:activity": self.activity_id,
                    "prov:time": self.generated_at,
                }
            },
            "wasAssociatedWith": {
                f"{self.activity_id}:agent": {
                    "prov:activity": self.activity_id,
                    "prov:agent": self.agent_id,
                }
            },
            "used": used,
        }

    def content_hash(self) -> str:
        return hashlib.sha256(str(self.to_w3c_prov()).encode("utf-8")).hexdigest()
