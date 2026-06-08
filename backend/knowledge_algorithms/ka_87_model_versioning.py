"""
KA-087: Model Versioning
Purpose: Manage and track different versions of machine learning models, ensuring reproducibility and artifact integrity.
"""
import logging
import json
import os
import hashlib
from typing import Dict, Any, Optional
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA087VersioningInput(BaseModel):
    artifact: str = Field(..., description="The path to the model artifact to version")
    current_version: str = Field("0.0.0", description="Current semantic version to increment")
    artifact_hash: Optional[str] = Field(None, description="Precomputed artifact digest")
    source_commit: Optional[str] = Field(None, description="Source commit associated with the artifact")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Artifact metadata that participates in fallback hashing")

class KA087ModelVersioning(KnowledgeAlgorithm):
    """
    KA-087: ML artifact versioning and registry tracking engine.
    """
    input_schema = KA087VersioningInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-087"
        self.config = {**self._load_config(), **context}

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_87_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA087VersioningInput) -> Dict[str, Any]:
        artifact_path = input_data.artifact
        self.log_execution_step("Versioning Model Artifact", {"path": artifact_path})
        
        scheme = self.config.get("versioning_scheme", "semver")
        artifact_digest = input_data.artifact_hash or self._artifact_digest(artifact_path, input_data.metadata)
        new_version = self._next_version(input_data.current_version)
        
        return {
            "success": True,
            "version_assigned": new_version,
            "scheme_used": scheme,
            "registry_path": self.config.get("artifact_registry_path", "/mnt/registry"),
            "artifact_hash": artifact_digest,
            "git_commit": input_data.source_commit or artifact_digest[:7],
            "artifact_exists": os.path.exists(artifact_path),
        }

    @staticmethod
    def _next_version(current_version: str) -> str:
        version = current_version.strip().lstrip("v")
        parts = version.split(".")
        numeric = []
        for part in parts[:3]:
            try:
                numeric.append(int(part))
            except ValueError:
                numeric.append(0)
        while len(numeric) < 3:
            numeric.append(0)
        numeric[2] += 1
        return f"v{numeric[0]}.{numeric[1]}.{numeric[2]}"

    @staticmethod
    def _artifact_digest(artifact_path: str, metadata: Dict[str, Any]) -> str:
        if os.path.exists(artifact_path) and os.path.isfile(artifact_path):
            digest = hashlib.sha256()
            with open(artifact_path, "rb") as artifact_file:
                for chunk in iter(lambda: artifact_file.read(1024 * 1024), b""):
                    digest.update(chunk)
            return digest.hexdigest()

        fallback_payload = json.dumps(
            {"artifact": artifact_path, "metadata": metadata},
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(fallback_payload.encode("utf-8")).hexdigest()

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA087ModelVersioning(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-087 Failed: {e}")
        return {"success": False, "error": str(e)}
