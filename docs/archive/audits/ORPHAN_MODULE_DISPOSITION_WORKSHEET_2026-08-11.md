# Orphan Module Disposition Worksheet

| Field | Value |
|---|---|
| Date | 2026-08-11 |
| Scope | `.pyc` bytecode **without** matching `.py` on the main tree |
| Count | **78 unique** modules (`backend` + `core` + Python SDK) |
| Purpose | Owner review: **wire back in** vs **legacy / delete residue** |
| Method | Orphan scan + live importer check + worktree source survival + prior product decisions |

## How to use this sheet

For each row, mark **Disposition**:

| Code | Meaning |
|---|---|
| **DELETE** | Not needed on current product; remove pyc (and empty dirs); do not restore |
| **HOLD** | Leave residue for now, or keep idea for later — but **do not wire** without a decision |
| **WIRE** | Restore source from worktree/history and integrate into live path |
| **SUPERSEDED** | Already replaced by a different live module; delete orphan only |

**Default recommendation** below is audit judgment aligned with:

- Single-owner desktop auth (no multi-tenant SaaS RBAC/MFA)
- Cloud BYOK generative on mainline (unless you choose otherwise)
- Live injection screening via gateway / `prompt_injection_shield` / `ai_guardrail` (not `defense_supervisor`)
- Models live in root `models.py`
- Canonical personas = `backend/dsqp` + live `core/persona/quad`
- Thin SDK (no client-side provider brain)

---

## Executive summary (recommended defaults)

| Bucket | Count (approx) | Recommendation |
|---|---:|---|
| Security multi-user / SaaS era | 14 | **DELETE** (already product-decided for several) |
| Local model + gateway tier chain | 10 | **HOLD → product decision** (wire only if local generative is a goal) |
| Consolidated routes / models / services | 15 | **SUPERSEDED → DELETE pyc** |
| Axes renames / old axis names | 6 | **SUPERSEDED → DELETE pyc** |
| Old persona engines | 6 | **SUPERSEDED → DELETE pyc** |
| MCP jira/salesforce | 2 | **DELETE** unless you want those connectors now |
| Core simulation / KA residue | 5 | **DELETE** (live sim is elsewhere) |
| SDK client providers + handlers | 8 | **DELETE** (thin SDK; providers server-owned) |
| Misc legacy backend modules | ~12 | **DELETE** |

**Nothing in the orphan list is required for the current live desktop path** as audited.
The only **strategic** wire-back candidate is **local model acceleration** (plus related tier modules) **if** you want airgapped generative again.

---

## A. Security orphans (SaaS / multi-user era)

Live security today is desktop + content defense, **not** this set:

`ai_guardrail`, `prompt_injection_shield`, `content_defense`, `desktop_local_auth`, `dpapi_store`, `encryption_manager`, `session_manager`, …

| Module | Dir | Pyc date | Prior decision / notes | Default | Your mark |
|---|---|---|---|---|---|
| `defense_supervisor` | `backend/security` | 2026-07-05 | **DECIDED deprecate** in `CODEX_WORK_QUEUE` C-6 / D-2. Live path uses gateway + shield/guardrail. Wiring = duplicate fail-open surface. Source still in worktree. | **DELETE** | |
| `mfa` | `backend/security` | 2026-05-13 | Web MFA removed with desktop single-owner auth | **DELETE** | |
| `rbac` | `backend/security` | 2026-06-13 | Multi-role SaaS; not single-owner desktop | **DELETE** | |
| `tenant_rls` | `backend/security` | 2026-05-13 | Explicitly removed in auth deprecation Phase D | **DELETE** | |
| `honeypot` | `backend/security` | 2026-05-13 | Prior audit: delete (attacker decoy, dead single-mode) | **DELETE** | |
| `context_aware` | `backend/security` | 2026-05-13 | Prior: dup of retired defense supervisor / Crescendo | **DELETE** | |
| `api_security` | `backend/security` | 2026-05-22 | Prior: HMAC for retired enterprise gateway | **DELETE** | |
| `security_monitoring` | `backend/security` | 2026-05-13 | Prior: SIEM multi-user | **DELETE** | |
| `zero_trust` | `backend/security` | 2026-05-13 | Enterprise SaaS framing; not wired | **DELETE** | |
| `token_manager` | `backend/security` | 2026-05-13 | Legacy token surface | **DELETE** | |
| `active_defense` | `backend/security` | 2026-05-13 | Not on live path | **DELETE** | |
| `sanitizer` | `backend/security` | 2026-05-13 | Likely superseded by `prompt_injection_shield` / middleware | **DELETE** | |
| `data_classification` | `backend/security` | 2026-05-13 | Prior audit **kept for future compliance** (PII/GDPR classifier) but still unwired | **HOLD** (idea) / **DELETE pyc** until you design wiring | |
| `vulnerability_scanner` | `backend/security` | 2026-05-13 | Prior: kept for CVE/SBOM future; still unwired | **HOLD** (idea) / **DELETE pyc** until you design wiring | |

**Recommendation:** Delete all security orphan pyc. If you care about future PII classifier / SBOM, track as **new features** from requirements, not by resurrecting opaque pyc.

---

## B. Local generative stack (only real “maybe wire” cluster)

Electron today hard-stubs local models as unavailable (“cloud-only product”).
Full source survives in:

`.claude/worktrees/stupefied-ramanujan-516b57/backend/local_model_acceleration/`

| Module | Dir | Pyc date | Notes | Default | Your mark |
|---|---|---|---|---|---|
| `config` | `local_model_acceleration` | 2026-06-27 | Part of Ollama/local stack | **HOLD / DECIDE** | |
| `keepalive` | same | 2026-06-27 | | **HOLD / DECIDE** | |
| `manager` | same | 2026-06-27 | | **HOLD / DECIDE** | |
| `ollama_client` | same | 2026-06-27 | | **HOLD / DECIDE** | |
| `paths` | same | 2026-06-27 | | **HOLD / DECIDE** | |
| `response_cache` | same | 2026-06-27 | | **HOLD / DECIDE** | |
| `safety` | same | 2026-06-27 | | **HOLD / DECIDE** | |
| `complexity_classifier` | `backend/llm_gateway` | 2026-06-27 | Local-tier routing companion | **HOLD / DECIDE** | |
| `escalation_config` | `backend/llm_gateway` | 2026-06-27 | T0 Ollama → cloud tiers (historical) | **HOLD / DECIDE** | |
| `tier_availability` | `backend/llm_gateway` | 2026-06-27 | | **HOLD / DECIDE** | |

### Owner decision (required)

| Option | Meaning |
|---|---|
| **B0 — Accept cloud-BYOK only** | Mark all of §B **DELETE**. Align docs/UI (already partially honest). Airgap = data plane, not generative. |
| **B1 — Restore local generative** | Mark §B **WIRE**. Restore `.py` from worktree, tests, Electron status truth, server-owned only (SDK stays thin). |

Do **not** leave pyc as a half-feature.

---

## C. Routes / models / services (consolidated — delete residue)

| Module | Dir | Notes | Default | Your mark |
|---|---|---|---|---|
| `storage_download_routes` | `backend/routes` | Folded into `storage_routes.py` | **SUPERSEDED → DELETE** | |
| `storage_management_routes` | `backend/routes` | Same | **SUPERSEDED → DELETE** | |
| `storage_upload_routes` | `backend/routes` | Same | **SUPERSEDED → DELETE** | |
| `gateway` | `backend/models` | Models live in root `models.py` | **SUPERSEDED → DELETE** | |
| `knowledge` | `backend/models` | Same | **SUPERSEDED → DELETE** | |
| `mcp` | `backend/models` | Same | **SUPERSEDED → DELETE** | |
| `simulation` | `backend/models` | Same | **SUPERSEDED → DELETE** | |
| `trace` | `backend/models` | Same | **SUPERSEDED → DELETE** | |
| `truth` | `backend/models` | Same | **SUPERSEDED → DELETE** | |
| `user` | `backend/models` | Same | **SUPERSEDED → DELETE** | |
| `file_upload_service` | `backend/services` | Prior: superseded by multimodal route hardening | **DELETE** | |
| `email_service` | `backend` | Multi-user auth emails; not desktop | **DELETE** | |
| `export_service` | `backend` | Prior: route-level export supersedes | **DELETE** | |
| `admin` | `backend` | Old admin module; live admin is routes + gateway admin | **DELETE** | |
| `app_factory` | `backend` | Superseded by `app.py` `create_app` | **DELETE** | |
| `decorators` | `backend` | Live: `backend/auth/api_decorators.py` | **DELETE** | |
| `enterprise_architecture` | `backend` | Dead enterprise module | **DELETE** | |
| `security_scan_api` | `backend` | Unregistered; old API | **DELETE** | |
| `ka_management` | `backend/api` | Live KA via `ka_routes` + controller | **DELETE** | |
| `blueprint` | `backend/tracing` | Live: `backend/tracing/api.py` | **DELETE** | |
| `asgi_security` | `backend/middleware` | Flask path uses other middleware | **DELETE** | |
| `input_sanitizer` | `backend/middleware` | Likely superseded | **DELETE** | |
| `request_hooks` | `backend/middleware` | Large dead hooks module | **DELETE** | |

---

## D. MCP connector orphans

| Module | Dir | Notes | Default | Your mark |
|---|---|---|---|---|
| `jira` | `backend/mcp_server/tools` | CHANGELOG: removed from production connector set | **DELETE** | |
| `salesforce` | `backend/mcp_server/tools` | Same | **DELETE** | |

**Wire only if** you actively want Jira/Salesforce connectors on the desktop product now (qualification + consent path required). Source may exist in older worktrees.

---

## E. Axes orphans (renames / old names)

Live axis files use the **current** naming (e.g. `axis3_honeycomb.py`, `axis4_branch.py`, `axis14_acquisition_lifecycle.py`, `axis17_frost_mode.py`).

Orphan pyc are **old names**:

| Module | Notes | Default | Your mark |
|---|---|---|---|
| `axis3_domain` | Renamed → branch axis (`axis4_branch`) | **SUPERSEDED → DELETE** | |
| `axis5_honeycomb` | Renamed → `axis3_honeycomb` (see CODEX work queue C-1) | **SUPERSEDED → DELETE** | |
| `axis14_provenance` | Old A14 name; live = `axis14_acquisition_lifecycle` | **SUPERSEDED → DELETE** | |
| `axis15_object_type` | Old A15; live = `axis15_risk_threat` | **SUPERSEDED → DELETE** | |
| `axis16_validation_state` | Old A16; live = `axis16_ethics_trust` | **SUPERSEDED → DELETE** | |
| `axis17_security` | Old A17; live = `axis17_frost_mode` | **SUPERSEDED → DELETE** | |

Do **not** wire old names alongside new ones — that re-creates dual axis definitions.

---

## F. Persona / DSQP residue

| Module | Dir | Notes | Default | Your mark |
|---|---|---|---|---|
| `quad_persona_engine` | `core/persona` | Pre-DSQP / old engine; live DSQP + `core/persona/quad` | **DELETE** | |
| `persona_manager` | `core/persona` | Old | **DELETE** | |
| `persona_system` | `core/persona` | Old | **DELETE** | |
| `persona_models` | `core/persona` | Tiny stub residue | **DELETE** | |
| `memory_system` | `core/persona` | Old persona memory | **DELETE** | |
| `axis_role_mapper` | `core/persona/quad` | Old mapper; check live quad package before any wire | **DELETE** unless live import appears | |

Canonical live persona path: **`backend/dsqp`**.

---

## G. Simulation / KA / truth residue

| Module | Dir | Notes | Default | Your mark |
|---|---|---|---|---|
| `simulation_engine` | `backend/simulation` | Live sim uses `multi_agent_engine`, jobs, contracts, etc. | **DELETE** | |
| `coordinate_system` | `core/simulation` | Live coordinate system is `core/coordinate_system.py` | **DELETE** | |
| `pov_engine_enterprise` | `core/simulation` | Live: `pov_engine.py` etc. | **DELETE** | |
| `query_analysis_system` | `core/simulation` | Residue | **DELETE** | |
| `resilience_router` | `core/knowledge_algorithm` | Residue | **DELETE** | |
| `ka_50_knowledge_integrity_validator` | `backend/knowledge_algorithms` | Old KA module layout | **DELETE** | |
| `persona_sufficiency` | `backend/truth_engine/truth_core` | Unwired truth fragment | **DELETE** | |
| `router` | `backend/truth_engine/truth_core` | Unwired; gateway is authority | **DELETE** | |
| `rag_sanitizer` | `core/security` | Residue | **DELETE** | |

---

## H. Python SDK orphans (thin-client era)

SDK intentionally **stopped** owning providers / second stacks (v0.6+).

| Module | Dir | Notes | Default | Your mark |
|---|---|---|---|---|
| `handlers` | `ukg_sdk/ka` | Old KA handlers | **DELETE** | |
| `anthropic` | `ukg_sdk/providers` | Client-side provider | **DELETE** | |
| `azure_openai` | providers | | **DELETE** | |
| `base` | providers | | **DELETE** | |
| `google` | providers | | **DELETE** | |
| `local_slm` | providers | | **DELETE** | |
| `ollama` | providers | | **DELETE** | |
| `openai` | providers | | **DELETE** | |

Also remove empty `providers/` package after purge. Rebuild/publish SDK artifacts separately if needed.

---

## I. Quick decision checklist (owner)

Answer these three; everything else can follow defaults:

### 1) Local generative?

- [ ] **B0** Cloud BYOK only → delete all §B residue
- [ ] **B1** Restore Ollama/local stack → wire §B from worktree with tests

### 2) Future compliance tooling (`data_classification`, `vulnerability_scanner`)?

- [ ] Not now → **DELETE** pyc
- [ ] Want later as **new** design → **DELETE** pyc now, open a feature note (do not resurrect pyc)

### 3) Jira / Salesforce MCP?

- [ ] Not needed → **DELETE**
- [ ] Needed soon → **WIRE** from history with consent/qualification

If you leave all three as “not now / defaults,” the disposition is:

> **Delete all 78 orphan pyc clusters; wire nothing.**

---

## J. Safe cleanup procedure (after you mark the sheet)

1. **Do not** “fix” by restoring from pyc alone.
2. For **DELETE / SUPERSEDED**: remove `__pycache__` orphan files (and empty package dirs with only pyc).
3. Add/extend `config/legacy-retirement.json` entries for major clusters (security multi-user, local_model_acceleration, sdk providers, storage route split).
4. Optional CI/script: fail if new orphan pyc appears without matching `.py`.
5. For **WIRE** items only: copy **source** from worktree/git history → tests → registration → then delete pyc leftovers.
6. Run: targeted unit tests + `tests/security/test_security_module_wiring.py` + gateway/desktop smoke.

### Suggested purge commands (PowerShell, after owner sign-off)

Review paths first; do not run until dispositions are marked:

```powershell
# Example: purge known-safe security orphans (after DELETE decision)
$securityOrphans = @(
  'defense_supervisor','mfa','rbac','tenant_rls','honeypot','context_aware',
  'api_security','security_monitoring','zero_trust','token_manager',
  'active_defense','sanitizer','data_classification','vulnerability_scanner'
)
# Then remove matching backend\security\__pycache__\*.pyc files only
```

(Use a small script that only deletes pyc whose basename has no sibling `.py`.)

---

## K. Source survival map (if you choose WIRE)

| Cluster | Source still available? |
|---|---|
| `local_model_acceleration` + gateway tier modules | Yes — `.claude/worktrees/stupefied-ramanujan-516b57/` |
| `defense_supervisor` | Yes in worktree — **but product decision is deprecate** |
| MFA / RBAC / zero_trust / tenant_rls / honeypot | Older worktrees (`dazzling-antonelli`, `strange-margulis-cc69c5`) |
| Jira / Salesforce tools | Older worktrees |
| `email_service` / `security_scan_api` | Older worktrees |
| Axes old names | Not needed — live renames exist on main |
| Historical `backend/models/` split | Not needed — root `models.py` |

Worktrees are **gitignored agent caches** — treat as recovery archive, not product.

---

## L. Sign-off

| Role | Name | Date | Notes |
|---|---|---|---|
| Product owner | | | B0/B1 + checkboxes in §I |
| Implementer | | | Cleanup PR after marks |

---

## M. Full inventory list (all 78)

For checklist completeness (basename only):

**backend root:** admin, app_factory, decorators, email_service, enterprise_architecture, export_service, security_scan_api

**backend/api:** ka_management

**backend/knowledge_algorithms:** ka_50_knowledge_integrity_validator

**backend/llm_gateway:** complexity_classifier, escalation_config, tier_availability

**backend/local_model_acceleration:** config, keepalive, manager, ollama_client, paths, response_cache, safety

**backend/mcp_server/tools:** jira, salesforce

**backend/middleware:** asgi_security, input_sanitizer, request_hooks

**backend/models:** gateway, knowledge, mcp, simulation, trace, truth, user

**backend/routes:** storage_download_routes, storage_management_routes, storage_upload_routes

**backend/security:** active_defense, api_security, context_aware, data_classification, defense_supervisor, honeypot, mfa, rbac, sanitizer, security_monitoring, tenant_rls, token_manager, vulnerability_scanner, zero_trust

**backend/services:** file_upload_service

**backend/simulation:** simulation_engine

**backend/tracing:** blueprint

**backend/truth_engine/truth_core:** persona_sufficiency, router

**core/axes:** axis14_provenance, axis15_object_type, axis16_validation_state, axis17_security, axis3_domain, axis5_honeycomb

**core/knowledge_algorithm:** resilience_router

**core/persona:** memory_system, persona_manager, persona_models, persona_system, quad_persona_engine

**core/persona/quad:** axis_role_mapper

**core/security:** rag_sanitizer

**core/simulation:** coordinate_system, pov_engine_enterprise, query_analysis_system

**sdk providers/ka:** handlers, anthropic, azure_openai, base, google, local_slm, ollama, openai

Machine-readable scan: `.codex_tmp/orphan_pyc_inventory.json` (local, not authority).

---

**Bottom line for your review:**
Almost everything orphaned is **intentionally retired residue**. The only cluster worth a real wire-or-not debate is **local model acceleration**. Everything else should be **delete residue / do not rewire** unless you explicitly reopen multi-tenant SaaS, Jira/SF connectors, or a new compliance feature design.
