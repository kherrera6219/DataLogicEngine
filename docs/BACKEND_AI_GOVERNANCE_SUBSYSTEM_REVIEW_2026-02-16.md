# Backend/API + AI Governance Subsystem Review (2026-02-16)

## Scope
- Audited codebase: `C:/software/DataLogicEngine`
- Focus areas:
  - Backend/API Subsystems (12 items)
  - AI Governance Subsystems (7 items)
- Standard baseline: 2025 production expectations for security, reliability, and governance controls.
- Method:
  - Code inspection across `app.py`, `backend/`, `routes/`, and `models.py`
  - Runtime sweep via targeted backend/security tests

## Executive Summary
- Total controls reviewed: 19
- `Implemented`: 0
- `Partial`: 15
- `Missing`: 4
- Highest-risk issues:
  - No standardized `/live` and `/ready` endpoints
  - No canonical `/metrics` endpoint for infrastructure scraping
  - Prompt governance is not versioned/registry-driven
  - Error normalization is inconsistent; multiple routes return raw internal/provider error strings
  - LLM usage telemetry has a model mismatch risk (`_record_usage` writes fields not present in `LLMProviderUsage`)

## 3. Backend / API Subsystems
| Subsystem | Status | Evidence | 2025 Gap | Suggested Actions |
|---|---|---|---|---|
| Structured Logging System (JSON + redaction) | Partial | JSON + redaction exists in `backend/logging_config.py:20` and `backend/logging_config.py:82`; only call site found is definition (`rg configure_structured_logging`) while runtime uses `logging.basicConfig` in `app.py:39`. | Structured logger exists but is not wired into app startup. | Initialize `configure_structured_logging(app)` in boot path, keep correlation IDs in JSON fields, and add regression tests that assert PII redaction and JSON schema. |
| Request Correlation ID Middleware | Partial | Flask correlation middleware configured via `backend/middleware/__init__.py:159`, headers in `backend/middleware/correlation_id.py:20`; FastAPI services only have request logging middleware (`backend/api_gateway/api_gateway.py:79`, `backend/webhook_server/webhook_server.py:72`, `backend/model_context/model_context_server.py:152`). | Correlation is not enforced uniformly across Flask + FastAPI services. | Add shared ASGI correlation middleware and propagate `X-Request-ID` end-to-end across internal service calls. |
| Centralized Input Validation Layer | Partial | Multiple schema/validator systems exist (`backend/schemas/__init__.py`, `backend/utils/validation.py`), but many handlers still parse `request.json` directly (examples in `routes/api_routes.py` and many `routes/*`). | Validation is fragmented; schema enforcement is inconsistent. | Standardize one validation approach per framework (Pydantic/Marshmallow), require schema validation for all write endpoints, and gate in CI. |
| Rate Limiting & Resource Governor | Partial | Global limit configured in `app.py:120`; selective route limits in `routes/admin_routes.py` and `routes/user_data_routes.py`; API key RPM/daily limits in `backend/llm_gateway/api.py:158`; body/time limits in `backend/middleware/request_limits.py:46` and `backend/middleware/timeout.py:56`. | Good base controls, but no central tenant-level resource governor for concurrency/cost/load shedding. | Add tenant-aware resource governance (concurrency caps, queue backpressure, circuit policies) and publish limit headers consistently. |
| AI Request Timeout & Retry Controller | Partial | Retries implemented with backoff in `backend/llm_gateway/gateway.py:217`; provider timeout config stored in model/API (`models.py:509`, `backend/llm_gateway/api.py:563`) but not enforced in call path (`backend/llm_gateway/gateway.py:809`). | Timeout policy is configurable but not applied at execution time. | Enforce provider `timeout_seconds` with `asyncio.wait_for`, use per-provider `max_retries`, and classify retryable vs non-retryable failures. |
| Model Allowlist & Routing Engine | Partial | API key allowlists enforced in `backend/llm_gateway/api.py:107`; routing filters in `backend/llm_gateway/gateway.py:163` and tier routing logic in `_get_eligible_providers`. | Routing is code-heuristic based, not policy-governed/versioned. | Introduce declarative routing policy packs (tenant/risk/domain aware), with versioned policy rollout and auditability. |
| Health Check Endpoints (`/live`, `/ready`) | Missing | Health exists as `/health` (`app.py:526`, `backend/api_gateway/api_gateway.py:99`, `backend/webhook_server/webhook_server.py:92`, `backend/model_context/model_context_server.py:179`); repo search found no `"/live"` or `"/ready"` routes. | Liveness/readiness split is absent. | Add `/live` (process up) and `/ready` (deps ready) to each service; include dependency probes and explicit failure reasons. |
| Metrics Endpoint (`/metrics`) | Missing | Non-standard metrics routes exist (`backend/api/ka_management.py:194`, `backend/tracing/api.py:244`) but no canonical scrape endpoint. | No Prometheus/OpenTelemetry metrics surface at `/metrics`. | Add service-level `/metrics` with stable names/labels and low-cardinality dimensions; define auth strategy per deployment mode. |
| Localhost Authentication Layer (per-install secret) | Partial | Desktop autologin is loopback + header gated (`routes/auth_routes.py:24`, `routes/auth_routes.py:300`, `routes/auth_routes.py:316`). | Missing per-install secret/challenge; header alone is not sufficient for strong local trust. | Add per-install secret (DPAPI-backed), signed challenge/nonce, replay TTL, and explicit session binding. |
| CSRF Protection Layer | Partial | CSRF defaults disabled (`app.py:237`), custom origin-based protection for session-auth API requests (`app.py:252`, `app.py:265`), form CSRF enforced (`app.py:285`). | Origin check is useful but weaker than explicit token-based JSON CSRF defense. | Add double-submit CSRF tokens for session-auth JSON routes and enforce explicit allowlist for state-changing endpoints. |
| Security Headers Middleware | Partial | Flask security header middleware is wired (`backend/middleware/__init__.py:163`, `backend/security/security_headers.py:15`); FastAPI services do not apply equivalent hardening and use wildcard CORS (`backend/api_gateway/api_gateway.py:35`, `backend/webhook_server/webhook_server.py:35`, `backend/model_context/model_context_server.py:38`). | Header hardening is not consistent across service types; CORS wildcard remains on FastAPI services. | Add shared ASGI security-headers middleware, replace wildcard CORS with explicit allowlists, and unify CSP policy per environment. |
| Error Normalization Layer (no raw provider leaks) | Partial | Global normalized handlers exist (`app.py:604` onward), but raw `str(e)` responses remain (examples: `routes/api_routes.py:116`, `routes/api_routes.py:183`, `backend/webhook_server/webhook_server.py:181`, `backend/llm_gateway/api.py:328`, `backend/llm_gateway/api.py:655`). | Internal/provider errors can leak in API responses. | Enforce one error envelope and error-code mapping layer; block raw exception strings in responses via tests/lint rule. |

## 4. AI Governance Subsystems
| Subsystem | Status | Evidence | 2025 Gap | Suggested Actions |
|---|---|---|---|---|
| Prompt Template Registry (versioned prompts) | Missing | Prompts are mostly code-embedded (`backend/truth_engine/truth_core/personas.py:30`, `backend/quad_persona/quad_engine.py:23`) or single-file loaded (`backend/security/active_defense.py:32`); `MCPPrompt` exists but has no first-class version field (`models.py:1499`). | No canonical versioned prompt registry with lifecycle controls. | Build centralized prompt registry (`prompt_id`, `version`, `owner`, `approval_state`, changelog), immutable history, and runtime pinning. |
| Model Routing Policy Engine | Partial | Routing logic is tier/heuristic driven in `backend/llm_gateway/gateway.py` (`_get_eligible_providers`, policy filters at `:163`). | Policy is not externalized, versioned, or governance-audited. | Move routing to declarative policy engine with signed policy bundles and per-tenant/risk-domain constraints. |
| Guardrail Layer (prompt injection + moderation) | Partial | `PromptInjectionShield` exists (`backend/security/prompt_injection_shield.py:13`) but has no runtime references outside that module; `AIGuardrailService` is only wired in AGI planner path (`backend/truth_engine/truth_core/agi_planner.py:28`). | Guardrail coverage is not universal; no explicit moderation service path. | Add mandatory pre-input and post-output guardrail chain for all LLM entrypoints, including moderation scoring and deterministic block/transform actions. |
| AI Output Classification System | Missing | No dedicated output-classification module or endpoint-level classification hook found in runtime path. | Output risk/sensitivity classing is absent. | Implement output classifier taxonomy (safety/compliance/sensitivity/PII risk) and gate high-risk classes. |
| AI Usage Tracking & Cost Monitor | Partial | Usage endpoint and token aggregation exist (`backend/llm_gateway/api.py:740`); usage records model tracks tokens (`models.py:553`). However `_record_usage` sends `error_code` and `error_message` kwargs (`backend/llm_gateway/gateway.py:846`) not present on `LLMProviderUsage` model (`models.py:553-568`). | Cost governance is incomplete and telemetry reliability is at risk due schema mismatch. | Fix usage model mismatch immediately, add explicit cost accounting by provider/model, and publish daily tenant spend summaries. |
| Token Budget Enforcement System | Partial | API-key token cap per request (`backend/llm_gateway/api.py:111`), tenant budget manager (`backend/truth_engine/truth_gate/budget.py:14`) and budget APIs (`backend/truth_engine/api.py:284`). | Budget controls are split across systems; no single token budget authority across all AI paths. | Introduce centralized token-budget service with hard/soft thresholds, downgrade policy, and enforcement hooks in every model call path. |
| AI Metadata Audit Trail (model, version, timestamp) | Partial | Trace model supports model/version metadata (`models.py:664`, `models.py:690`), but gateway trace creation currently sets `model_name` only (`backend/llm_gateway/gateway.py` run creation around `:764`) and omits `model_version`. | Metadata capture is incomplete and not mandatory at write time. | Make model/provider/version/timestamp mandatory in trace writes; reject incomplete trace events and add audit integrity checks. |

## Recommended Phased Actions
### Phase 1 (0-30 days): Critical Hardening
1. Implement `/live`, `/ready`, and standardized `/metrics` endpoints across Flask and FastAPI services.
2. Fix error normalization leaks by banning raw `str(e)` in API responses.
3. Wire structured JSON logging with redaction in app bootstrap.
4. Fix `LLMProviderUsage` schema mismatch in gateway usage logging.
5. Enforce provider timeout + per-provider retry settings in LLM execution path.

### Phase 2 (31-60 days): Governance Consolidation
1. Build centralized prompt registry with prompt versioning and approval workflow.
2. Externalize model-routing rules into versioned policy bundles.
3. Deploy unified guardrail chain for all LLM entry points.
4. Standardize validation middleware and require schema validation on all write routes.

### Phase 3 (61-90 days): Enterprise Controls
1. Add per-install localhost authentication secret + challenge/nonce flow.
2. Deploy centralized token/cost governance with tenant dashboards and alerts.
3. Make metadata audit trail mandatory and integrity-verified.
4. Align Flask and FastAPI security-header/CORS posture under one policy baseline.

## Debugging / Error Sweep (This Review)
- Command:
  - `python -m pytest -q tests/security/test_security_headers.py tests/security/test_request_limits.py tests/test_health_endpoint.py tests/integration/test_llm_gateway_coverage.py --no-cov`
- Result:
  - `14 passed`

- Command:
  - `python -m pytest -q tests/security/test_active_defense.py tests/test_security_hardening.py tests/integration/test_truth_engine_api.py --no-cov`
- Result:
  - `20 passed, 1 warning`
  - Warning source: `backend/security/audit_logger.py` transaction state warning during integration test.

- Note:
  - Initial run without `--no-cov` failed only due global coverage gate (`fail-under=70`), not test assertion failures.

