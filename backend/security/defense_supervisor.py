"""
Defense Supervisor — LLM-backed semantic security screening.

Complements the pattern-based shields (``prompt_injection_shield`` and
``ai_guardrail``) with an LLM judgement step that can catch what regexes
cannot: Crescendo (gradual context poisoning), social engineering, and
novel DAN-style override phrasings.

Design constraints:

- Screening runs on the user's selected cloud model (OpenAI ``gpt-5.5`` or
  Google ``gemini-3.1-pro-preview``) via
  ``backend.llm_gateway.active_model.generate_with_active_model``. Note that
  the screened user input is therefore sent to the configured cloud provider.
- **Fail-open**: if no cloud model is configured, the model call fails, the
  model output is not parseable JSON, or the feature is disabled via
  ``DEFENSE_SUPERVISOR_ENABLED=false``, screening returns an ALLOW verdict
  flagged ``available: False``. The pattern-based shields in
  ``AIGovernanceEngine.prepare_request`` still run on every request.
- The supervisor prompt lives at ``backend/security/prompts/
  defense_supervisor.txt`` and is bundled into the installer through the
  ``('backend', 'backend')`` datas entry in ``backend.spec``.
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "defense_supervisor.txt"

_VALID_ACTIONS = {"ALLOW", "BLOCK", "HONEYPOT"}
_VALID_THREAT_TYPES = {
    "None",
    "Prompt Injection",
    "Crescendo",
    "Social Engineering",
    "Unsafe Tool",
}

# Default per-call generation timeout. Screening sits in the request path,
# so a slow model call must not stall chat for the full 30 s client default.
_SCREEN_TIMEOUT_SECONDS = 8


def _allow_verdict(reason: str, *, available: bool) -> dict[str, Any]:
    return {
        "is_safe": True,
        "threat_score": 0.0,
        "threat_type": "None",
        "reason": reason,
        "recommended_action": "ALLOW",
        "available": available,
    }


class DefenseSupervisor:
    """LLM security supervisor over the user's selected cloud model."""

    def __init__(self, client: Any | None = None, model: str | None = None) -> None:
        self._client = client
        self._model = model
        self._prompt_cache: str | None = None

    # ------------------------------------------------------------------
    # Prompt / availability
    # ------------------------------------------------------------------

    def load_prompt(self) -> str:
        """Return the supervisor system prompt (cached after first read)."""
        if self._prompt_cache is None:
            self._prompt_cache = _PROMPT_PATH.read_text(encoding="utf-8")
        return self._prompt_cache

    @staticmethod
    def enabled() -> bool:
        """Master switch — defaults on; set DEFENSE_SUPERVISOR_ENABLED=false to disable."""
        return os.environ.get("DEFENSE_SUPERVISOR_ENABLED", "true").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    def _complete(self, payload: str) -> str | None:
        """Return the model's raw JSON verdict text, or ``None``.

        Uses an injected client when provided (tests); otherwise the user's
        selected cloud model. Never raises.
        """
        if self._client is not None:
            try:
                result = self._client.generate(
                    model=self._model or "cloud",
                    prompt=payload,
                    system=self.load_prompt(),
                    format_json=True,
                    timeout_seconds=_SCREEN_TIMEOUT_SECONDS,
                    options={"temperature": 0},
                )
                if not result.get("ok"):
                    return None
                return result.get("response", "")
            except Exception as exc:  # noqa: BLE001
                logger.debug("Defense supervisor injected client failed open: %s", exc)
                return None
        try:
            from backend.llm_gateway.active_model import generate_with_active_model

            return generate_with_active_model(
                payload, system=self.load_prompt(), temperature=0.0, max_tokens=400
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("Defense supervisor screening failed open: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Screening
    # ------------------------------------------------------------------

    def screen(
        self,
        user_input: str,
        *,
        context_summary: str = "",
        user_role: str = "user",
    ) -> dict[str, Any]:
        """
        Screen *user_input* and return the supervisor verdict dict::

            {
                "is_safe": bool,
                "threat_score": float,        # 0.0-1.0
                "threat_type": str,           # one of _VALID_THREAT_TYPES
                "reason": str,
                "recommended_action": str,    # ALLOW | BLOCK | HONEYPOT
                "available": bool,            # False when screening was skipped
            }

        Never raises; every failure path returns a fail-open ALLOW verdict
        with ``available: False``.
        """
        if not self.enabled():
            return _allow_verdict("defense supervisor disabled", available=False)

        try:
            payload = json.dumps(
                {
                    "user_input": user_input,
                    "context_summary": context_summary,
                    "user_role": user_role,
                },
                ensure_ascii=False,
            )
            raw = self._complete(payload)
            if not raw:
                return _allow_verdict("no cloud model available", available=False)
            verdict = self._parse_verdict(raw)
            if verdict is None:
                return _allow_verdict("supervisor returned unparseable output", available=False)
            return verdict
        except Exception as exc:  # noqa: BLE001
            logger.warning("Defense supervisor screening failed open: %s", exc)
            return _allow_verdict(f"supervisor error: {exc}", available=False)

    @staticmethod
    def _parse_verdict(raw: str) -> dict[str, Any] | None:
        """Parse and normalize the model's JSON verdict; None if invalid."""
        text = (raw or "").strip()
        if not text:
            return None
        # Tolerate prose-wrapped JSON by extracting the first object literal.
        if not text.startswith("{"):
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return None
            text = match.group(0)
        try:
            data = json.loads(text)
        except Exception:
            return None
        if not isinstance(data, dict):
            return None

        try:
            threat_score = max(0.0, min(1.0, float(data.get("threat_score", 0.0))))
        except (TypeError, ValueError):
            threat_score = 0.0

        action = str(data.get("recommended_action", "ALLOW")).strip().upper()
        if action not in _VALID_ACTIONS:
            action = "ALLOW"
        # Honor the prompt's critical rule even if the model forgot it.
        if threat_score > 0.8 and action == "ALLOW":
            action = "BLOCK"

        threat_type = str(data.get("threat_type", "None")).strip()
        if threat_type not in _VALID_THREAT_TYPES:
            threat_type = "Prompt Injection" if action != "ALLOW" else "None"

        return {
            "is_safe": bool(data.get("is_safe", action == "ALLOW")),
            "threat_score": threat_score,
            "threat_type": threat_type,
            "reason": str(data.get("reason", "")),
            "recommended_action": action,
            "available": True,
        }


_supervisor: DefenseSupervisor | None = None


def get_defense_supervisor() -> DefenseSupervisor:
    """Return the process-wide DefenseSupervisor singleton."""
    global _supervisor  # noqa: PLW0603
    if _supervisor is None:
        _supervisor = DefenseSupervisor()
    return _supervisor
