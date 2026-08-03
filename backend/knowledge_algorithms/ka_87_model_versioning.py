"""KA-087: deterministic model-version registration proposals."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
import re
from typing import Any, Literal

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger(__name__)

_SEMVER = re.compile(r"^v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


class KA087VersioningInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "artifact_name": "qualified.onnx",
                    "artifact_sha256": "a" * 64,
                    "current_version": "v1.0.0",
                }
            ]
        },
    )

    artifact_name: str = Field(min_length=1, max_length=200)
    artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    current_version: str = Field(pattern=_SEMVER.pattern)
    increment: Literal["patch", "minor", "major"] = "patch"
    source_commit: str | None = Field(
        default=None,
        pattern=r"^[0-9a-f]{7,64}$",
    )
    release_channel: Literal["candidate", "staging", "production"] = (
        "candidate"
    )

    @field_validator("artifact_name")
    @classmethod
    def _file_name_only(cls, value: str) -> str:
        if Path(value).name != value:
            raise ValueError("artifact_name must be a file name")
        return value


class KA087ModelVersioning(KnowledgeAlgorithm):
    """Propose a semantic version without writing a registry or tag."""

    input_schema = KA087VersioningInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-087"

    def _run_logic(self, input_data: KA087VersioningInput) -> dict[str, Any]:
        proposed_version = self._next_version(
            input_data.current_version,
            input_data.increment,
        )
        request = {
            "artifact_name": input_data.artifact_name,
            "artifact_sha256": input_data.artifact_sha256,
            "current_version": input_data.current_version,
            "proposed_version": proposed_version,
            "increment": input_data.increment,
            "source_commit": input_data.source_commit,
            "release_channel": input_data.release_channel,
        }
        plan_sha256 = hashlib.sha256(
            json.dumps(
                request,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        self.log_execution_step(
            "Proposing Model Version Registration",
            {
                "artifact_name": input_data.artifact_name,
                "proposed_version": proposed_version,
            },
        )
        return {
            "success": True,
            "schema_version": "dle.model-version-proposal.v1",
            "status": "PROPOSED",
            "plan_sha256": plan_sha256,
            "proposed_version": proposed_version,
            "request": request,
            "version_assigned": False,
            "registry_write_applied": False,
            "tag_write_applied": False,
            "artifact_created": False,
        }

    @staticmethod
    def _next_version(current_version: str, increment: str) -> str:
        match = _SEMVER.fullmatch(current_version)
        if match is None:  # pragma: no cover - Pydantic enforces the shape
            raise ValueError("current_version must be semantic versioning")
        major, minor, patch = (int(value) for value in match.groups())
        if increment == "major":
            major, minor, patch = major + 1, 0, 0
        elif increment == "minor":
            minor, patch = minor + 1, 0
        else:
            patch += 1
        return f"v{major}.{minor}.{patch}"


def run(context: dict[str, Any]) -> dict[str, Any]:
    try:
        return KA087ModelVersioning(context).run(context)
    except Exception as exc:  # pragma: no cover - legacy adapter boundary
        logger.error("KA-087 failed: %s", exc)
        return {"success": False, "error": str(exc)}
