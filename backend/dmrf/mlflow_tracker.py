"""Optional DMRF MLflow tracking with a local JSONL fallback."""

from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
from typing import Any


class DMRFMLflowTracker:
    """Track DMRF runs without making MLflow a hard desktop dependency."""

    def __init__(self, tracking_uri: str | None = None):
        self.tracking_uri = tracking_uri or self.default_tracking_uri()

    @staticmethod
    def default_tracking_uri() -> str:
        configured = os.environ.get("MLFLOW_TRACKING_URI")
        if configured:
            return configured
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        return str(base / "DataLogicEngine" / "mlruns")

    def record(self, result: Any) -> dict[str, Any]:
        payload = {
            "run_id": result.run_id,
            "tier": result.tier,
            "ok": result.ok,
            "step_count": len(result.steps),
            "frost_depth": result.axis_vector.frost_layer_depth if result.axis_vector else 0,
            "created_at": datetime.now(UTC).isoformat(),
        }
        try:
            import mlflow  # type: ignore

            mlflow.set_tracking_uri(self.tracking_uri)
            mlflow.set_experiment("dmrf")
            with mlflow.start_run(run_name=result.run_id):
                mlflow.log_params({"tier": result.tier, "ok": str(result.ok)})
                mlflow.log_metrics(
                    {
                        "step_count": float(payload["step_count"]),
                        "frost_depth": float(payload["frost_depth"]),
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
        uri = self.tracking_uri
        if uri.startswith("file:"):
            uri = uri[5:]
        return Path(uri) / "dmrf_runs.jsonl"
