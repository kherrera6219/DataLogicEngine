"""LLM-assisted DSQP answer generation.

The DSQP novelty (`docs/ip/dsqp_technical_disclosure.md`) is that each persona's
seven role-construction components are *derived from the query* at runtime, not
filled from a per-axis template. This module realizes that substantively: one
structured cloud-model call per persona axis answers all seven self-questioning
questions for the specific query, coordinate, and domain.

Design constraints:

- **Cloud model.** Persona construction runs on the user's selected cloud model
  (OpenAI ``gpt-5.6-sol`` or Google ``gemini-3.7-flash``) via
  ``generate_with_active_model``.
- **Fail-safe to deterministic.** If the feature is disabled, no cloud model is
  configured, the call errors, or the model returns malformed output, the
  generator returns only the components it could validate; the chain fills the
  rest from the deterministic offline scaffold, so DSQP stays deterministic and
  offline-capable by default.
- **Schema-preserving.** Generated components match the exact nested shapes the
  deterministic path produces, so the validator and downstream L5 / SDK overlay
  consumers are unaffected.

Enable with ``DSQP_LLM_ASSISTED=true``. The canonical governed path keeps this
off unless an enhanced request has explicit consent and a separately accounted
provider-call budget.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)

# Per-component "primary" field that must be present and non-empty for the
# generated component to be accepted. Anything else falls back to deterministic.
_REQUIRED_FIELD: dict[str, str] = {
    "job_role": "title",
    "education": "degree",
    "certifications": "list",
    "skills": "items",
    "training": "modules",
    "career_path": "stages",
    "related_jobs": "overlapping_roles",
}

_LIST_FIELDS = {"list", "items", "modules", "stages", "overlapping_roles", "blind_spot_coverage", "constraints"}

# Generation sits in the persona-construction path (4 axes, run concurrently by
# the orchestrator); keep the per-axis budget bounded so a slow model degrades
# to the deterministic scaffold rather than stalling a chat turn. Tunable via
# DSQP_GENERATION_TIMEOUT for slower local hardware.
try:
    _GENERATION_TIMEOUT_SECONDS = max(3, int(os.environ.get("DSQP_GENERATION_TIMEOUT", "15")))
except (TypeError, ValueError):
    _GENERATION_TIMEOUT_SECONDS = 15

_SYSTEM_PROMPT = (
    "You construct an expert persona using the Dynamic Self-Questioning Protocol (DSQP).\n"
    "Given a user query, its coordinate path, risk domain, and a persona axis, answer the\n"
    "seven role-construction questions SPECIFICALLY for this query — not generic labels.\n"
    "The job role, degree, certifications, skills, training, career path, and related jobs\n"
    "must reflect the actual subject matter of the query (e.g. a query about cardiac implant\n"
    "clearance yields a medical-device regulatory role with FDA-specific credentials, not a\n"
    "generic 'Regulatory Analyst').\n\n"
    "Return ONLY a JSON object with exactly these keys and shapes:\n"
    "{\n"
    '  "job_role": {"title": str, "level": str, "focus_area": str},\n'
    '  "education": {"degree": str, "focus": str},\n'
    '  "certifications": {"list": [str], "required_for": str},\n'
    '  "skills": {"items": [str], "domain_focus": str},\n'
    '  "training": {"modules": [str], "risk_domain": str},\n'
    '  "career_path": {"stages": [str], "years_in_field": int},\n'
    '  "related_jobs": {"overlapping_roles": [str], "blind_spot_coverage": [str]}\n'
    "}\n"
    "Titles, degrees, certifications and skills must be concrete and query-specific."
)


class DSQPAnswerGenerator:
    """Generate query-derived persona component answers on the local model."""

    def __init__(self, client: Any | None = None, model: str | None = None) -> None:
        self._client = client
        self._model = model

    @staticmethod
    def enabled(context: dict[str, Any] | None = None) -> bool:
        """Return whether this request explicitly authorizes cloud DSQP work."""

        context = context or {}
        request_value = context.get("dsqp_llm_assisted")
        if request_value is not None:
            return str(request_value).strip().lower() in {"1", "true", "yes", "on"}
        return os.environ.get("DSQP_LLM_ASSISTED", "false").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    def _complete(self, prompt: str) -> str | None:
        """Return the model's raw JSON text, or ``None``.

        Uses an injected client when one is provided (tests / custom backends);
        otherwise calls the user's selected cloud model. Never raises.
        """
        if self._client is not None:
            try:
                result = self._client.generate(
                    model=self._model or "cloud",
                    prompt=prompt,
                    system=_SYSTEM_PROMPT,
                    format_json=True,
                    timeout_seconds=_GENERATION_TIMEOUT_SECONDS,
                    options={"temperature": 0.2},
                )
                if not result.get("ok"):
                    logger.debug("DSQP generation unavailable: %s", result.get("error"))
                    return None
                return result.get("response", "")
            except Exception as exc:  # noqa: BLE001
                logger.debug("DSQP injected client failed open: %s", exc)
                return None
        try:
            from backend.llm_gateway.active_model import generate_with_active_model

            return generate_with_active_model(
                prompt, system=_SYSTEM_PROMPT, temperature=0.2, max_tokens=900
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("DSQP answer generation failed open: %s", exc)
            return None

    def generate(
        self,
        *,
        persona_type: str,
        query: str,
        coordinate_path: str,
        keywords: list[str],
        context: dict[str, Any],
        questions: dict[str, str],
    ) -> dict[str, dict[str, Any]]:
        """Return ``{component_key: answer}`` for components the model produced
        and validated. Missing/invalid components are simply absent — the caller
        fills them deterministically. Never raises.
        """
        if not self.enabled(context):
            return {}

        domain = str(context.get("risk_domain") or context.get("domain") or "standard")
        prompt = json.dumps(
            {
                "query": query,
                "coordinate_path": coordinate_path,
                "risk_domain": domain,
                "persona_axis": persona_type,
                "questions": questions,
                "query_keywords": keywords,
            },
            ensure_ascii=False,
        )
        raw = self._complete(prompt)
        if not raw:
            return {}
        return self._validated_components(raw)

    @classmethod
    def _validated_components(cls, raw: str) -> dict[str, dict[str, Any]]:
        data = cls._parse_json(raw)
        if not isinstance(data, dict):
            return {}
        accepted: dict[str, dict[str, Any]] = {}
        for component, required in _REQUIRED_FIELD.items():
            value = data.get(component)
            if not isinstance(value, dict):
                continue
            # Coerce first (a model may return a scalar where a list is expected),
            # then validate the coerced primary field is present and non-empty.
            coerced = cls._coerce(component, value)
            primary = coerced.get(required)
            if required in _LIST_FIELDS:
                if not isinstance(primary, list) or not primary:
                    continue
            elif not str(primary or "").strip():
                continue
            accepted[component] = coerced
        return accepted

    @staticmethod
    def _coerce(component: str, value: dict[str, Any]) -> dict[str, Any]:
        """Normalize list/scalar field types so the output matches the schema."""
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if key in _LIST_FIELDS:
                if isinstance(item, list):
                    cleaned[key] = [str(v).strip() for v in item if str(v).strip()]
                elif str(item or "").strip():
                    cleaned[key] = [str(item).strip()]
                else:
                    cleaned[key] = []
            else:
                cleaned[key] = item
        if component == "career_path":
            try:
                cleaned["years_in_field"] = int(cleaned.get("years_in_field") or 0)
            except (TypeError, ValueError):
                cleaned["years_in_field"] = 0
        return cleaned

    @staticmethod
    def _parse_json(raw: str) -> Any:
        text = (raw or "").strip()
        if not text:
            return None
        if not text.startswith("{"):
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return None
            text = match.group(0)
        try:
            return json.loads(text)
        except Exception:
            return None
