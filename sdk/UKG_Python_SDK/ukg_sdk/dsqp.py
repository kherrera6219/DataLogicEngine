"""Offline DSQP client for SDK consumers."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any


COMPONENT_KEYS = [
    "job_role",
    "education",
    "certifications",
    "skills",
    "training",
    "career_path",
    "related_jobs",
]

AXIS_PERSONA_TYPES = {
    8: "knowledge",
    9: "sector",
    10: "regulatory",
    11: "compliance",
}


class DSQPClient:
    """Offline-capable SDK DSQP client with optional live backend use."""

    def __init__(self, backend_url: str | None = None):
        self.backend_url = backend_url

    def construct(
        self,
        query: str,
        coordinate: dict[str, Any] | None = None,
        *,
        axis_number: int = 8,
        coordinate_path: str = "sdk.default",
    ) -> dict[str, Any]:
        if self.backend_url:
            try:
                return self._construct_live(
                    query,
                    coordinate or {},
                    axis_number=axis_number,
                    coordinate_path=coordinate_path,
                )
            except Exception as exc:
                return {
                    **self._construct_offline(query, coordinate or {}, axis_number, coordinate_path),
                    "live_backend_error": str(exc),
                }
        return self._construct_offline(query, coordinate or {}, axis_number, coordinate_path)

    def _construct_live(
        self,
        query: str,
        coordinate: dict[str, Any],
        *,
        axis_number: int,
        coordinate_path: str,
    ) -> dict[str, Any]:
        import httpx

        response = httpx.post(
            f"{self.backend_url.rstrip('/')}/api/v1/gateway/dsqp-persona-profiles",
            json={"query": query, "coordinate": coordinate, "axis_number": axis_number, "coordinate_path": coordinate_path},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Invalid DSQP backend response")
        return payload

    def _construct_offline(
        self,
        query: str,
        coordinate: dict[str, Any],
        axis_number: int,
        coordinate_path: str,
    ) -> dict[str, Any]:
        if axis_number not in AXIS_PERSONA_TYPES:
            return {
                "success": False,
                "error": f"DSQP supports persona axes 8-11, got {axis_number}",
                "axis_number": axis_number,
                "coordinate_path": coordinate_path,
            }
        persona_type = AXIS_PERSONA_TYPES[axis_number]
        template = self._template_for(persona_type)
        digest = hashlib.sha256(
            json.dumps(
                {
                    "axis_number": axis_number,
                    "coordinate_path": coordinate_path,
                    "query": query,
                    "persona_type": persona_type,
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()[:12]
        keywords = self._keywords(query, coordinate_path)
        components = {
            key: self._answer_component(key, persona_type, query, coordinate_path, keywords)
            for key in COMPONENT_KEYS
        }
        chain = [
            {
                "step": index,
                "component": key,
                "question": template.get("questions", {}).get(key, f"Define {key}."),
                "answer": components[key],
                "axis_number": axis_number,
                "persona_type": persona_type,
            }
            for index, key in enumerate(COMPONENT_KEYS, start=1)
        ]
        return {
            "success": True,
            "persona_id": f"dsqp_{axis_number}_{digest}",
            "axis_number": axis_number,
            "persona_type": persona_type,
            "name": components["job_role"]["title"],
            "description": f"DSQP-constructed {persona_type} persona for {coordinate_path}",
            "components": components,
            "dsqp_chain": chain,
            "coverage_score": 1.0,
            "metadata": {
                "coordinate_path": coordinate_path,
                "axis_vector": coordinate,
                "query_digest": hashlib.sha256(query.encode("utf-8")).hexdigest()[:16],
                "construction_mode": "sdk_offline",
            },
            "created_at": datetime.now(UTC).isoformat(),
        }

    @staticmethod
    def _keywords(query: str, coordinate_path: str) -> list[str]:
        terms = [term.strip(".,:;!?()[]{}").lower() for term in f"{query} {coordinate_path}".split()]
        return [term for term in terms if len(term) > 2][:8] or ["analysis"]

    @staticmethod
    def _answer_component(component_key: str, persona_type: str, query: str, coordinate_path: str, keywords: list[str]) -> dict[str, Any]:
        label = coordinate_path.replace("_", " ").replace(".", " / ")
        title_words = " ".join(word.title() for word in keywords[:3])
        if component_key == "job_role":
            return {"title": f"Lead {persona_type.title()} Analyst", "focus_area": label, "query_mission": query[:240]}
        if component_key == "education":
            return {"degree": f"Advanced {persona_type.title()} domain training", "focus": label}
        if component_key == "certifications":
            return {"list": [f"UKG {persona_type.title()} Practitioner", "Evidence Review Lead"]}
        if component_key == "skills":
            return {"items": sorted(set([title_words or "Analysis", "Verification", "Risk Review"]))}
        if component_key == "training":
            return {"modules": ["DSQP Role Activation", "UKG 17-Axis Reasoning", f"{persona_type.title()} Evidence Review"]}
        if component_key == "career_path":
            return {"stages": ["Analyst", f"{persona_type.title()} Specialist", f"Lead {persona_type.title()} Analyst"]}
        return {"overlapping_roles": ["Risk Manager", "Technical Lead", f"{persona_type.title()} Reviewer"]}

    @staticmethod
    def _template_for(persona_type: str) -> dict[str, Any]:
        path = Path(__file__).resolve().parent / "data" / "dsqp_templates" / f"{persona_type}.json"
        fallback = Path(__file__).resolve().parent / "data" / "dsqp_templates" / "default.json"
        for candidate in (path, fallback):
            try:
                if candidate.exists():
                    return json.loads(candidate.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"questions": {key: f"What {key} activates this persona?" for key in COMPONENT_KEYS}}
