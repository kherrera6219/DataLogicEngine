"""DMRF bridge to FROST snapshots."""

from __future__ import annotations

from typing import Any

from core.system.frost_service import FROSTService


class FROSTBridge:
    """Create and verify per-step DMRF FROST snapshots."""

    def __init__(self, frost: FROSTService | None = None):
        self.frost = frost or FROSTService()

    def snapshot_step(self, step_name: str, state: dict[str, Any]) -> dict[str, Any]:
        snapshot_id = self.frost.snapshot(state, metadata={"dmrf_step": step_name})
        return {
            "snapshot_id": snapshot_id,
            "verified": self.frost.verify_snapshot(snapshot_id),
        }

    def status(self) -> dict[str, Any]:
        return self.frost.check_health()

