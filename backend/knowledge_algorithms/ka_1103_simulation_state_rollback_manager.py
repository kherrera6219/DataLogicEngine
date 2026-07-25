"""KA-1103: deterministic simulation rollback planning."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class SimulationCheckpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checkpoint_id: str = Field(min_length=1, max_length=200)
    sequence: int = Field(ge=0, le=1_000_000)
    state_sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    parent_checkpoint_id: str | None = Field(default=None, max_length=200)
    verified: bool


class KA1103Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "simulation_id": "simulation-1",
                    "current_checkpoint_id": "c2",
                    "target_checkpoint_id": "c1",
                    "checkpoints": [
                        {
                            "checkpoint_id": "c1",
                            "sequence": 1,
                            "state_sha256": "a" * 64,
                            "verified": True,
                        },
                        {
                            "checkpoint_id": "c2",
                            "sequence": 2,
                            "state_sha256": "b" * 64,
                            "parent_checkpoint_id": "c1",
                            "verified": True,
                        },
                    ],
                }
            ]
        },
    )

    simulation_id: str = Field(min_length=1, max_length=200)
    current_checkpoint_id: str = Field(min_length=1, max_length=200)
    target_checkpoint_id: str = Field(min_length=1, max_length=200)
    checkpoints: list[SimulationCheckpoint] = Field(min_length=1, max_length=10_000)

    @model_validator(mode="after")
    def validate_chain(self) -> KA1103Input:
        identifiers = [item.checkpoint_id for item in self.checkpoints]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("checkpoint IDs must be unique")
        known = set(identifiers)
        if self.current_checkpoint_id not in known or self.target_checkpoint_id not in known:
            raise ValueError("current and target checkpoints must exist")
        if any(
            item.parent_checkpoint_id and item.parent_checkpoint_id not in known
            for item in self.checkpoints
        ):
            raise ValueError("checkpoint parent is unknown")
        return self


class KA1103SimulationStateRollbackManager(KnowledgeAlgorithm):
    """Validate ancestry and create a rollback plan without changing state."""

    input_schema = KA1103Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1103"

    def _run_logic(self, input_data: KA1103Input) -> dict[str, Any]:
        checkpoints = {item.checkpoint_id: item for item in input_data.checkpoints}
        path = []
        cursor = input_data.current_checkpoint_id
        seen = set()
        while cursor and cursor not in seen:
            seen.add(cursor)
            path.append(cursor)
            if cursor == input_data.target_checkpoint_id:
                break
            cursor = checkpoints[cursor].parent_checkpoint_id
        target = checkpoints[input_data.target_checkpoint_id]
        blockers = []
        if input_data.target_checkpoint_id not in path:
            blockers.append("target_not_ancestor")
        if not target.verified:
            blockers.append("target_not_verified")
        return {
            "success": True,
            "status": "simulation_rollback_evaluated",
            "simulation_id": input_data.simulation_id,
            "decision": "approve_plan" if not blockers else "block",
            "rollback_path": path if not blockers else [],
            "target_state_sha256": target.state_sha256,
            "blockers": blockers,
            "rollback_applied": False,
            "effect_service_required": True,
            "deterministic": True,
            "limitations": (
                "This validates declared checkpoint ancestry and integrity state. "
                "The simulation service must perform and verify rollback."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1103SimulationStateRollbackManager(context).run(context)
