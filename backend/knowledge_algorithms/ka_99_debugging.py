"""KA-099: bounded redacted diagnostic snapshot normalization."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from backend.knowledge_algorithms.production_utils import stable_identifier
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

SENSITIVE_KEYS = (
    "password",
    "secret",
    "token",
    "credential",
    "authorization",
    "private_key",
)


class DebugFrame(BaseModel):
    filename: str = Field(max_length=500)
    function: str = Field(max_length=500)
    line: int = Field(ge=0)
    locals: dict[str, Any] = Field(default_factory=dict)


class KA099DebugInput(BaseModel):
    error_context: str = Field(
        default="runtime_exception",
        min_length=1,
        max_length=2_000,
    )
    traceback_text: str | None = Field(default=None, max_length=100_000)
    frames: list[DebugFrame] = Field(default_factory=list, max_length=100)
    system_metrics: dict[str, Any] = Field(default_factory=dict)

    @field_validator("system_metrics")
    @classmethod
    def bound_metrics(cls, value: dict[str, Any]) -> dict[str, Any]:
        if len(value) > 200:
            raise ValueError("system_metrics exceeds 200 entries")
        return value


class KA099Debugging(KnowledgeAlgorithm):
    """Normalize already captured diagnostics without hidden frame inspection."""

    input_schema = KA099DebugInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-099"

    def _run_logic(self, input_data: KA099DebugInput) -> dict[str, Any]:
        frames = [
            {
                "filename": frame.filename.replace("\\", "/").rsplit("/", 1)[-1],
                "function": frame.function,
                "line": frame.line,
                "locals": self._redact(frame.locals),
            }
            for frame in input_data.frames
        ]
        snapshot = {
            "error_context": input_data.error_context,
            "traceback": input_data.traceback_text,
            "frames": frames,
            "system_metrics": self._redact(input_data.system_metrics),
        }
        return {
            "success": True,
            "snapshot_id": stable_identifier("debug", snapshot),
            "remote_port_active": False,
            "snapshot": snapshot,
            "capture_mode": "caller_supplied_redacted_diagnostics",
            "limitations": (
                "KA-099 does not inspect live caller frames, open a remote "
                "debug port, or persist a snapshot."
            ),
        }

    @classmethod
    def _redact(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                str(key): (
                    "[REDACTED]"
                    if any(token in str(key).lower() for token in SENSITIVE_KEYS)
                    else cls._redact(item)
                )
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [cls._redact(item) for item in value[:1_000]]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value if not isinstance(value, str) else value[:2_000]
        return f"<{type(value).__name__}>"


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA099Debugging(context).run(context)
