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

## Executive Summary (Final Status After Phases 1-3)
- Total controls reviewed: 19
- `Implemented`: 15
- `Partial`: 4
- `Missing`: 0
- Remaining high-priority gaps:
  - Structured logging is in place but multi-process/service bootstrap consistency is still maturing.
  - Centralized schema validation is deployed for critical paths but not yet universal across all write routes.
  - Rate limiting is strong at baseline but tenant-level concurrency governance is still limited.
  - Error normalization is enforced in gateway paths but not yet uniformly rolled out to every route family.

## Initial Baseline Snapshot (Pre-Implementation)
- Baseline controls before implementation pass:
  - `Implemented`: 0
  - `Partial`: 15
  - `Missing`: 4
- Highest-risk findings at baseline:
  - No standardized `/live` and `/ready` endpoints
  - No canonical `/metrics` endpoint for infrastructure scraping
  - Prompt governance was not versioned/registry-driven
  - Error normalization allowed raw internal/provider leak paths
  - LLM usage telemetry had a model mismatch risk (`_record_usage` wrote fields not present in `LLMProviderUsage`)

## 3. Backend / API Subsystems (Baseline Assessment)
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

## 4. AI Governance Subsystems (Baseline Assessment)
| Subsystem | Status | Evidence | 2025 Gap | Suggested Actions |
|---|---|---|---|---|
| Prompt Template Registry (versioned prompts) | Missing | Prompts are mostly code-embedded (`backend/truth_engine/truth_core/personas.py:30`, `backend/quad_persona/quad_engine.py:23`) or single-file loaded (`backend/security/active_defense.py:32`); `MCPPrompt` exists but has no first-class version field (`models.py:1499`). | No canonical versioned prompt registry with lifecycle controls. | Build centralized prompt registry (`prompt_id`, `version`, `owner`, `approval_state`, changelog), immutable history, and runtime pinning. |
| Model Routing Policy Engine | Partial | Routing logic is tier/heuristic driven in `backend/llm_gateway/gateway.py` (`_get_eligible_providers`, policy filters at `:163`). | Policy is not externalized, versioned, or governance-audited. | Move routing to declarative policy engine with signed policy bundles and per-tenant/risk-domain constraints. |
| Guardrail Layer (prompt injection + moderation) | Partial | `PromptInjectionShield` exists (`backend/security/prompt_injection_shield.py:13`) but has no runtime references outside that module; `AIGuardrailService` is only wired in AGI planner path (`backend/truth_engine/truth_core/agi_planner.py:28`). | Guardrail coverage is not universal; no explicit moderation service path. | Add mandatory pre-input and post-output guardrail chain for all LLM entrypoints, including moderation scoring and deterministic block/transform actions. |
| AI Output Classification System | Missing | No dedicated output-classification module or endpoint-level classification hook found in runtime path. | Output risk/sensitivity classing is absent. | Implement output classifier taxonomy (safety/compliance/sensitivity/PII risk) and gate high-risk classes. |
| AI Usage Tracking & Cost Monitor | Partial | Usage endpoint and token aggregation exist (`backend/llm_gateway/api.py:740`); usage records model tracks tokens (`models.py:553`). However `_record_usage` sends `error_code` and `error_message` kwargs (`backend/llm_gateway/gateway.py:846`) not present on `LLMProviderUsage` model (`models.py:553-568`). | Cost governance is incomplete and telemetry reliability is at risk due schema mismatch. | Fix usage model mismatch immediately, add explicit cost accounting by provider/model, and publish daily tenant spend summaries. |
| Token Budget Enforcement System | Partial | API-key token cap per request (`backend/llm_gateway/api.py:111`), tenant budget manager (`backend/truth_engine/truth_gate/budget.py:14`) and budget APIs (`backend/truth_engine/api.py:284`). | Budget controls are split across systems; no single token budget authority across all AI paths. | Introduce centralized token-budget service with hard/soft thresholds, downgrade policy, and enforcement hooks in every model call path. |
| AI Metadata Audit Trail (model, version, timestamp) | Partial | Trace model supports model/version metadata (`models.py:664`, `models.py:690`), but gateway trace creation currently sets `model_name` only (`backend/llm_gateway/gateway.py` run creation around `:764`) and omits `model_version`. | Metadata capture is incomplete and not mandatory at write time. | Make model/provider/version/timestamp mandatory in trace writes; reject incomplete trace events and add audit integrity checks. |

## Recommended Phased Actions (Baseline Plan)
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

## Phase 1 Implementation Update (2026-02-16)
Implemented in this pass:
1. Standardized service health + readiness + metrics endpoints.
   - Flask app: added `/live`, `/ready`, `/metrics` in `app.py`.
   - FastAPI services: added `/live`, `/ready`, `/metrics` in:
     - `backend/api_gateway/api_gateway.py`
     - `backend/webhook_server/webhook_server.py`
     - `backend/model_context/model_context_server.py`
   - Kept `/health` for backward compatibility while exposing readiness state.
2. Error normalization hardening for raw provider/internal leak prevention.
   - Removed raw exception payloads from:
     - `routes/api_routes.py`
     - `backend/webhook_server/webhook_server.py`
     - `backend/llm_gateway/api.py` (chat failure path, SSE stream errors, provider test endpoint)
   - Added gateway-facing error sanitization helper in `backend/llm_gateway/api.py`.
3. Structured JSON logging wired into Flask bootstrap.
   - App bootstrap now initializes `configure_structured_logging(app)` in `app.py`.
   - Middleware logging formatter override is skipped in JSON mode in `backend/middleware/__init__.py`.
   - Fixed formatter recursion risk by switching formatter redaction to non-logging redaction path in `backend/logging_config.py`.
4. LLM usage telemetry schema mismatch fixed.
   - Added `error_code` and `error_message` columns to `LLMProviderUsage` in `models.py`.
   - Hardened usage persistence path in `backend/llm_gateway/gateway.py`:
     - UUID parsing safety
     - backward-compatible fallback if DB schema lags
     - skip usage insert for synthetic non-DB providers
5. Provider timeout + per-provider retry controls enforced in gateway execution path.
   - `backend/llm_gateway/gateway.py` now enforces:
     - provider-specific `timeout_seconds` using `asyncio.wait_for`
     - provider-specific `max_retries`
     - retryability classification with bounded exponential backoff
     - failure usage recording with error classification (`PROVIDER_ERROR`, `TIMEOUT`, `EXCEPTION`)

Additional hardening included:
- Fixed duplicate `verify_token` override bug in `backend/model_context/model_context_server.py` (JWT validation dependency remains authoritative).
- Added regression tests for new health/metrics behavior and gateway retry/timeout behavior:
  - `tests/test_health_endpoint.py`
  - `tests/integration/test_llm_gateway_integration.py`
  - `tests/integration/test_gateway_api_coverage.py`

## Debugging / Error Sweep (Post-Implementation)
- Command:
  - `python -m compileall app.py backend/middleware/__init__.py backend/api_gateway/api_gateway.py backend/webhook_server/webhook_server.py backend/model_context/model_context_server.py routes/api_routes.py backend/llm_gateway/api.py backend/llm_gateway/gateway.py models.py tests/integration/test_gateway_api_coverage.py`
- Result:
  - compile succeeded for all targeted files.

- Command:
  - `python -m pytest -q tests/test_health_endpoint.py tests/integration/test_llm_gateway_coverage.py tests/integration/test_gateway_api_coverage.py tests/unit/test_llm_gateway_internal_units.py tests/integration/test_llm_gateway_integration.py --no-cov`
- Result:
  - `38 passed, 1 warning`.

- Command:
  - `python -m pytest -q tests/security/test_security_headers.py tests/security/test_request_limits.py tests/test_health_endpoint.py tests/integration/test_llm_gateway_coverage.py --no-cov`
- Result:
  - `17 passed, 1 warning`.

- Command:
  - `python -m pytest -q tests/security/test_active_defense.py tests/test_security_hardening.py tests/integration/test_truth_engine_api.py --no-cov`
- Result:
  - `20 passed, 2 warnings`.

- Notes:
  - Warning remained from `pythonjsonlogger` deprecation path (`pythonjsonlogger.jsonlogger` import path warning).
  - Existing SQLAlchemy warning persists in `tests/integration/test_truth_engine_api.py` (`backend/security/audit_logger.py` transaction state warning).

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

## Phase 2 Implementation Update (2026-02-16)
Implemented in this pass:
1. Localhost authentication hardening with per-install secret + one-time challenge/nonce.
   - Added desktop local auth security module:
     - `backend/security/desktop_local_auth.py`
   - Added desktop challenge endpoint and challenge verification enforcement:
     - `routes/auth_routes.py` (`/api/v1/auth/desktop/challenge`, `/api/v1/auth/desktop/auto-login`)
   - Updated desktop integration tests for signed challenge flow:
     - `tests/integration_routes/test_desktop_auto_login_security.py`
   - Wired Electron desktop runtime to:
     - persist install secret locally
     - pass secret to backend process
     - sign `X-Desktop-Auth-Nonce` as `X-Desktop-Auth-Signature` for loopback auth calls
     - `frontend/electron/main.ts`
   - Updated frontend API auto-login flow to request challenge nonce before desktop auto-login:
     - `frontend/lib/api/index.ts`

2. Session JSON CSRF token layer (double-submit style enforcement path).
   - Added API CSRF helper module:
     - `backend/security/api_csrf.py`
   - Added CSRF token issuance endpoint:
     - `routes/auth_routes.py` (`/api/v1/auth/csrf-token`)
   - Enforced token checks for session-authenticated state-changing API requests (production-default, env-controlled):
     - `app.py` (`ENFORCE_API_CSRF_TOKENS`)
   - Added frontend automatic CSRF token fetch/injection + retry refresh for state-changing non-desktop requests:
     - `frontend/lib/api/index.ts`

3. FastAPI security/correlation parity with Flask.
   - Added shared ASGI middleware:
     - `backend/middleware/asgi_security.py`
   - Applied middleware to FastAPI services:
     - `backend/api_gateway/api_gateway.py`
     - `backend/model_context/model_context_server.py`
     - `backend/webhook_server/webhook_server.py`

4. Centralized input validation + error normalization strengthening.
   - Added shared request validation utility:
     - `backend/utils/request_validation.py`
   - Added auth request schemas:
     - `backend/schemas/auth_schemas.py`
   - Migrated auth write endpoints to pydantic validation:
     - `routes/auth_routes.py`
   - Enforced gateway chat request schema validation:
     - `backend/llm_gateway/api.py`
   - Added shared public-error normalization utility and wired gateway/api:
     - `backend/utils/error_normalization.py`
     - `backend/llm_gateway/gateway.py`
     - `backend/llm_gateway/api.py`
   - Extended gateway message schema for multimodal compatibility and moved to pydantic v2 validator style:
     - `backend/llm_gateway/schemas.py`

### Debugging / Error Sweep (Phase 2)
- Commands:
  - `npm --prefix frontend run test -- tests/unit/lib/api/index.test.ts tests/unit/lib/api/auth.test.ts tests/unit/middleware.test.ts`
  - `npm --prefix frontend run electron:build`
  - `C:/software/DataLogicEngine/.venv/Scripts/python -m pytest tests/integration_routes/test_desktop_auto_login_security.py -q --no-cov`
  - `C:/software/DataLogicEngine/.venv/Scripts/python -m pytest tests/integration_routes -q --no-cov`
  - `C:/software/DataLogicEngine/.venv/Scripts/python -m pytest tests/unit/test_llm_gateway_internal_units.py -q --no-cov`
  - `C:/software/DataLogicEngine/.venv/Scripts/python -m pytest tests/security/test_security_headers.py -q --no-cov`
  - `C:/software/DataLogicEngine/.venv/Scripts/python -m py_compile app.py routes/auth_routes.py backend/middleware/asgi_security.py backend/security/api_csrf.py backend/security/desktop_local_auth.py backend/utils/error_normalization.py backend/utils/request_validation.py backend/llm_gateway/api.py backend/llm_gateway/gateway.py backend/llm_gateway/schemas.py backend/api_gateway/api_gateway.py backend/model_context/model_context_server.py backend/webhook_server/webhook_server.py`
- Results:
  - Frontend targeted tests: `22 passed`
  - Electron TS build: pass
  - Desktop auth integration tests: `5 passed`
  - Integration routes suite: `69 passed`
  - Gateway internal unit tests: `7 passed`
  - Security headers tests: `2 passed`
  - Python compile sweep: pass

## Phase 3 Implementation Update (2026-02-16)
Implemented in this pass:
1. Prompt template registry (versioned prompts) and routing policy registry.
   - Added registry models:
     - `models.py` (`PromptTemplate`, `ModelRoutingPolicy`)
   - Added admin APIs for list/create operations:
     - `backend/llm_gateway/api.py`
       - `GET/POST /api/admin/prompt-templates`
       - `GET/POST /api/admin/routing-policies`

2. Model routing policy engine + prompt-template application in gateway runtime.
   - Added governance runtime module:
     - `backend/llm_gateway/governance.py`
   - Gateway request pipeline now enforces:
     - prompt injection checks
     - optional prompt-template rendering (`prompt_template_key`, `prompt_template_version`)
     - policy allowlists (`routing_policy_name`, `routing_policy_version`)
     - token budget controls (per-request + daily envelope)
   - Integrated in:
     - `backend/llm_gateway/gateway.py`

3. Guardrail layer + AI output classification.
   - Added pre-input and post-output guardrail checks in governance engine.
   - Added output classification (`risk_level`, flags) and API response exposure:
     - `backend/llm_gateway/gateway.py`
     - `backend/llm_gateway/api.py` (`output_classification` in chat response)

4. AI usage tracking + cost monitor + token budget enforcement.
   - Added estimated cost field to usage model:
     - `models.py` (`LLMProviderUsage.estimated_cost_usd`)
   - Added model-based cost estimation and persisted usage cost:
     - `backend/llm_gateway/governance.py`
     - `backend/llm_gateway/gateway.py`
   - Extended usage analytics endpoint with cost summaries:
     - `backend/llm_gateway/api.py` (`total_estimated_cost_usd`, provider cost rollups)

5. AI metadata audit trail (model/version/timestamp + policy context).
   - Added audit model:
     - `models.py` (`AIAuditEvent`)
   - Added audit event writer in governance runtime:
     - `backend/llm_gateway/governance.py`
   - Added audit event recording in gateway success/failure/governance-block paths:
     - `backend/llm_gateway/gateway.py`
   - Added audit retrieval endpoint:
     - `GET /api/admin/ai-audit` in `backend/llm_gateway/api.py`
   - Trace enrichment:
     - `TraceRun.model_version` is now populated in `backend/llm_gateway/gateway.py`

6. Validation compatibility improvements for governance-enabled requests.
   - Gateway request schema now accepts multimodal message content while validating non-empty input:
     - `backend/llm_gateway/schemas.py`
   - Request-level validation remains enforced while preserving prior `400` behavior for missing model/messages:
     - `backend/llm_gateway/api.py`

### Debugging / Error Sweep (Phase 3)
- Commands:
  - `C:/software/DataLogicEngine/.venv/Scripts/python -m pytest tests/unit/test_llm_governance_engine.py -q --no-cov`
  - `C:/software/DataLogicEngine/.venv/Scripts/python -m pytest tests/unit/test_llm_gateway_internal_units.py tests/unit/test_llm_governance_engine.py tests/integration/test_gateway_api_coverage.py tests/integration/test_gateway_extended.py -q --no-cov`
  - `C:/software/DataLogicEngine/.venv/Scripts/python -m pytest tests/integration_routes -q --no-cov`
  - `C:/software/DataLogicEngine/.venv/Scripts/python -m py_compile models.py backend/llm_gateway/governance.py backend/llm_gateway/gateway.py backend/llm_gateway/api.py`
  - `npm --prefix frontend run test -- tests/unit/middleware.test.ts tests/unit/lib/api/index.test.ts tests/unit/lib/runtime/policy.test.ts tests/unit/lib/api/auth.test.ts`
  - `npm --prefix frontend run electron:build`
- Results:
  - Governance engine unit tests: `4 passed`
  - Gateway/API focused tests: `28 passed`
  - Integration routes suite: `69 passed`
  - Python compile sweep: pass
  - Frontend targeted tests: `27 passed`
  - Electron TS build: pass

## Final Commit-Gate Sweep (2026-02-16)
- Commands:
  - `C:/software/DataLogicEngine/.venv/Scripts/python -m pytest C:/software/DataLogicEngine/tests/integration_routes -q --no-cov`
  - `C:/software/DataLogicEngine/.venv/Scripts/python -m pytest C:/software/DataLogicEngine/tests/unit/test_llm_gateway_internal_units.py C:/software/DataLogicEngine/tests/unit/test_llm_governance_engine.py C:/software/DataLogicEngine/tests/integration/test_gateway_api_coverage.py C:/software/DataLogicEngine/tests/integration/test_gateway_extended.py -q --no-cov`
  - `C:/software/DataLogicEngine/.venv/Scripts/python -m py_compile C:/software/DataLogicEngine/app.py C:/software/DataLogicEngine/backend/api_gateway/api_gateway.py C:/software/DataLogicEngine/backend/llm_gateway/api.py C:/software/DataLogicEngine/backend/llm_gateway/gateway.py C:/software/DataLogicEngine/backend/llm_gateway/schemas.py C:/software/DataLogicEngine/backend/llm_gateway/governance.py C:/software/DataLogicEngine/backend/middleware/asgi_security.py C:/software/DataLogicEngine/backend/model_context/model_context_server.py C:/software/DataLogicEngine/backend/security/api_csrf.py C:/software/DataLogicEngine/backend/security/desktop_local_auth.py C:/software/DataLogicEngine/backend/utils/error_normalization.py C:/software/DataLogicEngine/backend/utils/request_validation.py C:/software/DataLogicEngine/backend/webhook_server/webhook_server.py C:/software/DataLogicEngine/routes/auth_routes.py C:/software/DataLogicEngine/models.py`
- Results:
  - Integration routes suite: `69 passed`
  - Gateway/API focused tests: `28 passed`
  - Python compile sweep: pass
