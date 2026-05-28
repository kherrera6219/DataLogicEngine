"""Local-first MLflow tracking for TruthMemory sessions."""

from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
from typing import Any


class TruthMemoryMLflowTracker:
    """Track TruthMemory sessions through MLflow when available, JSONL otherwise."""

    def __init__(self, tracking_uri: str | None = None):
        self.tracking_uri = tracking_uri or self.default_tracking_uri()

    @staticmethod
    def default_tracking_uri() -> str:
        configured = os.environ.get("MLFLOW_TRACKING_URI")
        if configured:
            return configured
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        return str(base / "DataLogicEngine" / "mlruns")

    def record_session(self, session_data: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "session_id": str(session_data.get("session_id") or ""),
            "tier": str(session_data.get("tier") or "unknown"),
            "confidence_score": float(session_data.get("confidence_score") or 0.0),
            "processing_time_ms": float(session_data.get("processing_time_ms") or 0.0),
            "created_at": datetime.now(UTC).isoformat(),
        }
        try:
            import mlflow  # type: ignore

            mlflow.set_tracking_uri(self.tracking_uri)
            mlflow.set_experiment("truthmemory")
            with mlflow.start_run(run_name=payload["session_id"] or None):
                mlflow.log_params({"tier": payload["tier"]})
                mlflow.log_metrics(
                    {
                        "confidence_score": payload["confidence_score"],
                        "processing_time_ms": payload["processing_time_ms"],
                    }
                )
            return {"tracked": True, "backend": "mlflow", "tracking_uri": self.tracking_uri}
        except Exception:
            path = self._fallback_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, sort_keys=True) + "\n")
            return {"tracked": True, "backend": "jsonl", "path": str(path)}

    def _fallback_path(self) -> Path:
        uri = self.tracking_uri[5:] if self.tracking_uri.startswith("file:") else self.tracking_uri
        return Path(uri) / "truthmemory_sessions.jsonl"
