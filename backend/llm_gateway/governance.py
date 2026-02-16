"""
AI governance controls for the LLM gateway execution path.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy import func

from backend.security.ai_guardrail import AIGuardrailService
from backend.security.prompt_injection_shield import validate_user_input


DEFAULT_MODEL_COSTS_USD_PER_1K = {
    "gpt-5": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.01, "output": 0.03},
    "gpt-5-mini": {"input": 0.002, "output": 0.006},
    "gpt-5-nano": {"input": 0.001, "output": 0.003},
    "gemini": {"input": 0.003, "output": 0.009},
    "claude": {"input": 0.008, "output": 0.024},
    "default": {"input": 0.002, "output": 0.006},
}


@dataclass
class GovernanceDecision:
    ok: bool
    query: str
    error: Optional[str] = None
    allowed_provider_types: set[str] = field(default_factory=set)
    allowed_models: set[str] = field(default_factory=set)
    prompt_template_key: Optional[str] = None
    prompt_template_version: Optional[str] = None
    routing_policy_name: Optional[str] = None
    routing_policy_version: Optional[str] = None
    estimated_request_tokens: int = 0
    governance_flags: list[str] = field(default_factory=list)


class AIGovernanceEngine:
    def __init__(self, db_session=None):
        self.db = db_session
        self.guardrail = AIGuardrailService()

    @staticmethod
    def _positive_int(value: Any, default: int, minimum: int = 1, maximum: int = 2_000_000) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        if parsed < minimum:
            return default
        return min(parsed, maximum)

    @staticmethod
    def _normalize_allowlist(values: Any) -> set[str]:
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, (list, tuple, set)):
            return set()
        normalized: set[str] = set()
        for value in values:
            if value is None:
                continue
            text = str(value).strip().lower()
            if text:
                normalized.add(text)
        return normalized

    @staticmethod
    def _estimate_prompt_tokens(text: str) -> int:
        return max(1, len(text or "") // 4)

    @staticmethod
    def _safe_format_template(template_body: str, variables: dict[str, Any]) -> str:
        class SafeDict(dict):
            def __missing__(self, key):
                return "{" + key + "}"

        return template_body.format_map(SafeDict(variables))

    def _resolve_prompt_template(self, template_key: str, version: Optional[str]):
        try:
            from models import PromptTemplate
        except Exception:
            return None

        query = PromptTemplate.query.filter_by(template_key=template_key, is_active=True)
        if version:
            template = query.filter_by(version=version).first()
            if template:
                return template
        return query.order_by(PromptTemplate.created_at.desc()).first()

    def _resolve_routing_policy(self, policy_name: str, version: Optional[str]):
        try:
            from models import ModelRoutingPolicy
        except Exception:
            return None

        query = ModelRoutingPolicy.query.filter_by(policy_name=policy_name, is_active=True)
        if version:
            policy = query.filter_by(version=version).first()
            if policy:
                return policy
        return query.order_by(ModelRoutingPolicy.created_at.desc()).first()

    def _daily_usage_tokens(self, user_id: Optional[int], api_key_id: Optional[str]) -> int:
        if not self.db:
            return 0
        if not user_id and not api_key_id:
            return 0
        try:
            from models import LLMProviderUsage
        except Exception:
            return 0

        start_of_day = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        query = self.db.query(
            func.coalesce(func.sum(LLMProviderUsage.tokens_in + LLMProviderUsage.tokens_out), 0)
        ).filter(LLMProviderUsage.created_at >= start_of_day)

        if user_id:
            query = query.filter(LLMProviderUsage.user_id == user_id)
        if api_key_id:
            try:
                query = query.filter(LLMProviderUsage.api_key_id == uuid.UUID(str(api_key_id)))
            except (TypeError, ValueError, AttributeError):
                pass

        try:
            return int(query.scalar() or 0)
        except Exception:
            return 0

    def prepare_request(self, request: Any, query: str) -> GovernanceDecision:
        normalized_query = str(query or "").strip()
        if not normalized_query:
            return GovernanceDecision(ok=False, query="", error="Empty user query")

        shield_result = validate_user_input(normalized_query, strict_mode=False)
        if not shield_result.get("is_safe", False):
            return GovernanceDecision(
                ok=False,
                query=normalized_query,
                error="Prompt blocked by guardrail policy",
                governance_flags=["prompt_injection_blocked"],
            )

        input_ok, input_reason = self.guardrail.validate_input(normalized_query)
        if not input_ok:
            return GovernanceDecision(
                ok=False,
                query=normalized_query,
                error=input_reason or "Prompt blocked by guardrail policy",
                governance_flags=["guardrail_input_blocked"],
            )

        governance_flags: list[str] = []
        prompt_template_key = None
        prompt_template_version = None

        meta = request.meta if isinstance(request.meta, dict) else {}
        template_key = str(meta.get("prompt_template_key") or "").strip()
        template_version = str(meta.get("prompt_template_version") or "").strip() or None
        if template_key:
            template = self._resolve_prompt_template(template_key, template_version)
            if template:
                variables = meta.get("prompt_variables", {}) if isinstance(meta.get("prompt_variables"), dict) else {}
                rendered = self._safe_format_template(
                    template.template_body,
                    {
                        "user_query": normalized_query,
                        **variables,
                    },
                )
                normalized_query = rendered
                prompt_template_key = template.template_key
                prompt_template_version = template.version
                governance_flags.append("prompt_template_applied")

        allowed_models: set[str] = set()
        allowed_provider_types: set[str] = set()
        routing_policy_name = None
        routing_policy_version = None

        policy_name = str(meta.get("routing_policy_name") or "").strip()
        policy_version = str(meta.get("routing_policy_version") or "").strip() or None
        if policy_name:
            policy = self._resolve_routing_policy(policy_name, policy_version)
            if policy:
                policy_rules = policy.rules if isinstance(policy.rules, dict) else {}
                allowed_models = self._normalize_allowlist(policy_rules.get("allowed_models"))
                allowed_provider_types = self._normalize_allowlist(
                    policy_rules.get("allowed_provider_types") or policy_rules.get("allowed_providers")
                )
                routing_policy_name = policy.policy_name
                routing_policy_version = policy.version
                governance_flags.append("routing_policy_applied")

        estimated_prompt_tokens = self._estimate_prompt_tokens(normalized_query)
        estimated_completion_tokens = self._positive_int(request.max_tokens, 1024, minimum=1, maximum=64_000)
        estimated_request_tokens = estimated_prompt_tokens + estimated_completion_tokens

        per_request_budget = self._positive_int(
            meta.get("token_budget"),
            self._positive_int(os.environ.get("AI_TOKEN_BUDGET_PER_REQUEST"), 32_000, minimum=512, maximum=128_000),
            minimum=512,
            maximum=128_000,
        )
        if estimated_request_tokens > per_request_budget:
            return GovernanceDecision(
                ok=False,
                query=normalized_query,
                error="Token budget exceeded for this request",
                estimated_request_tokens=estimated_request_tokens,
                governance_flags=["request_budget_exceeded"],
            )

        daily_budget = self._positive_int(
            meta.get("daily_token_budget"),
            self._positive_int(os.environ.get("AI_DAILY_TOKEN_BUDGET_PER_USER"), 250_000, minimum=1_000),
            minimum=1_000,
        )
        used_tokens_today = self._daily_usage_tokens(request.user_id, request.api_key_id)
        if used_tokens_today + estimated_request_tokens > daily_budget:
            return GovernanceDecision(
                ok=False,
                query=normalized_query,
                error="Daily token budget exceeded",
                estimated_request_tokens=estimated_request_tokens,
                governance_flags=["daily_budget_exceeded"],
            )

        return GovernanceDecision(
            ok=True,
            query=normalized_query,
            allowed_provider_types=allowed_provider_types,
            allowed_models=allowed_models,
            prompt_template_key=prompt_template_key,
            prompt_template_version=prompt_template_version,
            routing_policy_name=routing_policy_name,
            routing_policy_version=routing_policy_version,
            estimated_request_tokens=estimated_request_tokens,
            governance_flags=governance_flags,
        )

    def classify_output(self, content: str) -> dict[str, Any]:
        text = str(content or "")
        lowered = text.lower()
        flags: list[str] = []
        risk_level = "low"

        if re.search(r"\b\d{3}-\d{2}-\d{4}\b", text):
            flags.append("possible_ssn")
            risk_level = "high"
        if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text):
            flags.append("contains_email")
            risk_level = "medium" if risk_level == "low" else risk_level
        if re.search(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b", text):
            flags.append("contains_phone")
            risk_level = "medium" if risk_level == "low" else risk_level
        if any(marker in lowered for marker in ("ignore previous instructions", "system prompt", "admin mode")):
            flags.append("prompt_leakage_pattern")
            risk_level = "high"

        return {
            "risk_level": risk_level,
            "flags": flags,
            "classified_at": datetime.now(UTC).isoformat(),
        }

    def apply_output_controls(self, content: str) -> tuple[str, dict[str, Any], list[str]]:
        output_ok, output_reason = self.guardrail.validate_output(content)
        warnings: list[str] = []
        final_output = content

        if not output_ok:
            final_output = "Response withheld by safety policy."
            warnings.append(output_reason or "Output blocked by guardrail")

        classification = self.classify_output(final_output)
        if classification["risk_level"] in {"medium", "high"}:
            warnings.append(f"Output classified as {classification['risk_level']} risk")

        return final_output, classification, warnings

    @staticmethod
    def estimate_cost_usd(model: str, tokens_in: int, tokens_out: int) -> float:
        pricing = DEFAULT_MODEL_COSTS_USD_PER_1K.copy()
        raw_pricing = os.environ.get("AI_MODEL_PRICING_USD_PER_1K")
        if raw_pricing:
            try:
                parsed = json.loads(raw_pricing)
                if isinstance(parsed, dict):
                    for key, value in parsed.items():
                        if isinstance(value, dict):
                            pricing[str(key).lower()] = {
                                "input": float(value.get("input", pricing["default"]["input"])),
                                "output": float(value.get("output", pricing["default"]["output"])),
                            }
            except Exception:
                pass

        normalized_model = (model or "").strip().lower()
        selected_rate = pricing["default"]
        for prefix, rate in pricing.items():
            if prefix == "default":
                continue
            if normalized_model.startswith(prefix):
                selected_rate = rate
                break

        in_cost = (max(0, int(tokens_in)) / 1000.0) * float(selected_rate["input"])
        out_cost = (max(0, int(tokens_out)) / 1000.0) * float(selected_rate["output"])
        return round(in_cost + out_cost, 8)

    def record_audit_event(self, **payload: Any) -> None:
        if not self.db:
            return
        try:
            from models import AIAuditEvent
            from extensions import db
        except Exception:
            return

        def parse_uuid(raw: Any) -> Optional[uuid.UUID]:
            if raw is None:
                return None
            if isinstance(raw, uuid.UUID):
                return raw
            try:
                return uuid.UUID(str(raw))
            except (TypeError, ValueError, AttributeError):
                return None

        try:
            event = AIAuditEvent(
                run_id=parse_uuid(payload.get("run_id")),
                user_id=payload.get("user_id"),
                api_key_id=parse_uuid(payload.get("api_key_id")),
                provider=payload.get("provider"),
                model=payload.get("model") or "unknown",
                model_version=payload.get("model_version") or "unknown",
                prompt_template_key=payload.get("prompt_template_key"),
                prompt_template_version=payload.get("prompt_template_version"),
                routing_policy_name=payload.get("routing_policy_name"),
                routing_policy_version=payload.get("routing_policy_version"),
                classification=payload.get("classification"),
                governance_flags=payload.get("governance_flags"),
                request_tokens_estimate=payload.get("request_tokens_estimate"),
                tokens_in=payload.get("tokens_in"),
                tokens_out=payload.get("tokens_out"),
                estimated_cost_usd=payload.get("estimated_cost_usd"),
                success=bool(payload.get("success", True)),
                error_code=payload.get("error_code"),
                error_message=payload.get("error_message"),
                event_metadata=payload.get("metadata"),
            )
            db.session.add(event)
            db.session.commit()
        except Exception:
            try:
                db.session.rollback()
            except Exception:
                pass
