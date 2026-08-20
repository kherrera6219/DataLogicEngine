"""
FROST (Fast Recording of Simulated Transactions) Snapshot & Delta Service

This module provides high-efficiency state management for the USKD.
It enables branching, snapshotting, and delta tracking of simulation states,
allowing for recursive reasoning and multi-path exploration.
"""

import logging
import json
import hashlib
import copy
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional

from core.security.integrity import (
    hmac_sha256_hex,
    resolve_hmac_secret,
    sha256_hex,
    verify_hmac_sha256,
)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class FROSTService:
    """
    FROST Service

    Responsibilities:
    1. Capture immutable snapshots of the system state.
    2. compute deltas between snapshots.
    3. Branch and merge states for parallel reasoning.
    4. Provide transactional integrity for nested simulations.

    Optional backend services are accepted via constructor so callers (and tests) can
    inject them directly, removing the need for lazy backend imports in method bodies.
    When not provided, each method attempts the lazy import as a fallback.
    """

    def __init__(
        self,
        object_store_getter: Optional[Any] = None,
        memory_service_getter: Optional[Any] = None,
        persist_objects: bool = True,
    ):
        self.logger = logging.getLogger(__name__)
        self._object_store_getter = object_store_getter
        self._memory_service_getter = memory_service_getter
        self._persist_objects = bool(persist_objects)

        # In-memory store of snapshots: snapshot_id -> state_dict
        self.snapshots: Dict[str, Dict[str, Any]] = {}
        self.snapshot_metadata: Dict[str, Dict[str, Any]] = {}

        # Delta store: target_id -> {base_id, delta}
        self.deltas: Dict[str, Dict[str, Any]] = {}
        
        # Branching info
        self.branches: Dict[str, str] = {} # branch_name -> last_snapshot_id

        # HMAC secret used to seal snapshots.
        self._hmac_secret = resolve_hmac_secret(
            "FROST_SNAPSHOT_HMAC_SECRET",
            fallback_envs=("SESSION_SECRET",),
        )

    def _generate_id(self, state: Dict[str, Any]) -> str:
        """Generate a deterministic snapshot ID based on state content."""
        state_str = json.dumps(state, sort_keys=True, cls=DateTimeEncoder)
        return f"snap_{hashlib.sha256(state_str.encode()).hexdigest()[:16]}"

    def snapshot(self, state: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Capture a snapshot of the current state.
        """
        snapshot_id = self._generate_id(state)
        state_copy = copy.deepcopy(state)
        
        if snapshot_id not in self.snapshots:
            # Deep copy to ensure immutability
            self.snapshots[snapshot_id] = state_copy
            self.logger.debug(f"Created snapshot: {snapshot_id}")
        else:
            state_copy = self.snapshots[snapshot_id]

        integrity_payload = {
            "snapshot_id": snapshot_id,
            "state": state_copy,
            "metadata": metadata or {},
        }
        content_sha256 = sha256_hex(integrity_payload)
        signature = hmac_sha256_hex(integrity_payload, self._hmac_secret) if self._hmac_secret else None
        self.snapshot_metadata[snapshot_id] = {
            "algorithm": "sha256+hmac-sha256" if signature else "sha256",
            "content_sha256": content_sha256,
            "hmac_signature": signature,
            "signed_at": datetime.now(UTC).isoformat(),
            "metadata": copy.deepcopy(metadata) if metadata else {},
        }
        self._persist_snapshot_object(snapshot_id, state_copy)
        return snapshot_id

    def _persist_snapshot_object(self, snapshot_id: str, state: Dict[str, Any]) -> None:
        """Persist snapshots through the durable object materialization boundary."""
        if not self._persist_objects:
            self.snapshot_metadata[snapshot_id]["object_store"] = {
                "status": "in_memory_stage_snapshot",
                "snapshot_id": snapshot_id,
            }
            return
        try:
            key = f"{snapshot_id}.json"
            bundle = {
                "snapshot_id": snapshot_id,
                "state": state,
                "integrity": self.snapshot_metadata.get(snapshot_id, {}),
                "persisted_at": datetime.now(UTC).isoformat(),
            }
            metadata = {
                "artifact_type": "frost_snapshot",
                "snapshot_id": snapshot_id,
            }
            source_metadata = self.snapshot_metadata[snapshot_id].get("metadata") or {}
            for field in ("user_id", "tenant_id", "run_id"):
                if source_metadata.get(field) is not None:
                    metadata[field] = str(source_metadata[field])
            if self._object_store_getter is not None:
                payload = json.dumps(bundle, sort_keys=True, cls=DateTimeEncoder).encode("utf-8")
                store = self._object_store_getter()
                store.put(
                    "simulation-artifacts",
                    key,
                    payload,
                    content_type="application/json",
                    metadata=metadata,
                )
                reference = {
                    "bucket": "simulation-artifacts",
                    "key": key,
                    "size_bytes": len(payload),
                    "status": "ready",
                }
            else:
                from backend.storage.artifact_materialization import persist_object_artifact

                reference = persist_object_artifact(
                    entity_type="frost_snapshot",
                    entity_id=snapshot_id,
                    bucket="simulation-artifacts",
                    key=key,
                    body=bundle,
                    schema_version="frost-snapshot.v1",
                    content_type="application/json",
                    metadata=metadata,
                )
            self.snapshot_metadata[snapshot_id]["object_store"] = reference
        except Exception as exc:  # pylint: disable=broad-except
            from backend.storage.object_store import raise_if_object_store_required

            raise_if_object_store_required(exc, "simulation_write")
            self.logger.debug("FROST snapshot object persistence skipped: %s", exc)

    def verify_snapshot(self, snapshot_id: str) -> bool:
        """Verify snapshot hash/HMAC integrity."""
        state = self.snapshots.get(snapshot_id)
        integrity = self.snapshot_metadata.get(snapshot_id)
        if state is None or integrity is None:
            return False

        integrity_payload = {
            "snapshot_id": snapshot_id,
            "state": state,
            "metadata": integrity.get("metadata") or {},
        }
        expected_sha = integrity.get("content_sha256")
        actual_sha = sha256_hex(integrity_payload)
        if expected_sha != actual_sha:
            self.logger.error("Snapshot SHA integrity check failed: %s", snapshot_id)
            return False

        signature = integrity.get("hmac_signature")
        if signature:
            if not self._hmac_secret:
                self.logger.error("Snapshot %s includes signature but no HMAC secret is configured", snapshot_id)
                return False
            if not verify_hmac_sha256(integrity_payload, self._hmac_secret, signature):
                self.logger.error("Snapshot HMAC integrity check failed: %s", snapshot_id)
                return False
        return True

    def get_snapshot(self, snapshot_id: str, verify_integrity: bool = True) -> Optional[Dict[str, Any]]:
        """Retrieve a snapshot by ID."""
        snapshot = self.snapshots.get(snapshot_id)
        if snapshot is None:
            return None
        if verify_integrity and not self.verify_snapshot(snapshot_id):
            raise ValueError(f"Snapshot integrity verification failed for {snapshot_id}")
        return copy.deepcopy(snapshot)

    def diff(self, base_id: str, target_id: str) -> Dict[str, Any]:
        """
        Compute the delta between two snapshots.
        (Simple implementation using dict comparison)
        """
        if base_id not in self.snapshots or target_id not in self.snapshots:
            raise ValueError("Both snapshots must exist to compute diff")
            
        base = self.snapshots[base_id]
        target = self.snapshots[target_id]
        
        # Simple key-level diff
        delta = {
            "added": {},
            "modified": {},
            "removed": []
        }
        
        for k, v in target.items():
            if k not in base:
                delta["added"][k] = v
            elif base[k] != v:
                delta["modified"][k] = v
                
        for k in base:
            if k not in target:
                delta["removed"].append(k)
                
        return delta

    def apply(self, base_id: str, delta: Dict[str, Any]) -> str:
        """
        Apply a delta to a base snapshot to create a new one.
        """
        if base_id not in self.snapshots:
            raise ValueError(f"Base snapshot {base_id} not found")
            
        new_state = copy.deepcopy(self.snapshots[base_id])
        
        # Apply additions/modifications
        new_state.update(delta.get("added", {}))
        new_state.update(delta.get("modified", {}))
        
        # Apply removals
        for k in delta.get("removed", []):
            new_state.pop(k, None)
            
        return self.snapshot(new_state)

    def branch(self, snapshot_id: str, branch_name: str) -> str:
        """
        Create a new named branch from a snapshot.
        """
        if snapshot_id not in self.snapshots:
            raise ValueError(f"Snapshot {snapshot_id} not found")
            
        self.branches[branch_name] = snapshot_id
        self._checkpoint_memory_graph(branch_name)
        self.logger.info(f"Created branch '{branch_name}' at {snapshot_id}")
        return snapshot_id

    def rollback_memory_branch(self, branch_name: str) -> bool:
        """Restore the UnifiedMemoryService checkpoint captured for a branch."""
        try:
            if self._memory_service_getter is not None:
                get_unified_memory_service = self._memory_service_getter
            else:
                from backend.memory import get_unified_memory_service  # inversion:ok — injected or lazy optional memory service

            return get_unified_memory_service().restore(f"frost_branch:{branch_name}")
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.debug("FROST memory rollback skipped: %s", exc)
            return False

    def _checkpoint_memory_graph(self, branch_name: str) -> None:
        try:
            if self._memory_service_getter is not None:
                get_unified_memory_service = self._memory_service_getter
            else:
                from backend.memory import get_unified_memory_service  # inversion:ok — injected or lazy optional memory service

            get_unified_memory_service().checkpoint(f"frost_branch:{branch_name}")
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.debug("FROST memory checkpoint skipped: %s", exc)

    def merge(self, base_id: str, branch_snapshots: List[str], policy: str = "latest wins") -> str:
        """
        Merge multiple branch snapshots back into a base state.
        """
        current_state = copy.deepcopy(self.snapshots[base_id])
        
        for snap_id in branch_snapshots:
            if snap_id not in self.snapshots:
                continue
            
            branch_state = self.snapshots[snap_id]
            # Simple merge logic based on policy
            if policy == "latest wins":
                current_state.update(branch_state)
            # Future policy: "consensus" or "refinement" would go here
            
        return self.snapshot(current_state)

    def check_health(self) -> Dict[str, Any]:
        """System health check."""
        signed = sum(1 for data in self.snapshot_metadata.values() if data.get("hmac_signature"))
        verified = sum(1 for snapshot_id in self.snapshots if self.verify_snapshot(snapshot_id))
        return {
            "healthy": True,
            "snapshot_count": len(self.snapshots),
            "branch_count": len(self.branches),
            "signed_snapshots": signed,
            "verified_snapshots": verified,
        }
