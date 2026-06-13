# DataLogicEngine — Session Handoff

_Last updated: 2026-06-13 — **PHASE 1 COMPLETE (8/8); Phase 2 in progress.**
Done: Sprint 0, A4, A3, A1a, A1b, A2(+A2-2), A5, A6a, A6b (Phase 1); A7+A8
(knowledge_algorithms), A9 (quad persona), A10 (security), A11 (core/axes). N1 (SEKRE)
+ N2 (defense_supervisor) both wired._
_**A11 `core/axes/` DONE** (verify-only): 17 axes register correctly, Axis 5 unmanaged by
design (N4), N3/DUP-4 clean from Sprint 0; 30 axes tests pass._
_**A12 `backend/storage/` DONE**: DB-N/DB-C/DB-M all re-confirmed live; connection_manager
isn't rate-limiting (moot single-mode); **RT-10 fixed** (atomic settings write). 46 tests pass._
_**A13 `core/system/` DONE** (verify-only): all 11 services live; DUP-2 = 3 distinct
orchestrators (retained by design); SekreEngine (N1) wired live via system_initializer;
TV-6 Socket.IO is in gateway/websocket not trace_service. **Next: A14 `sdk/UKG_Python_SDK/`.**_
_**A10 `backend/security/` DONE.** Carry-overs A3-4/A5-2/SC-2 + password all resolved.
Single-mode/OS-auth reframe → multi-user auth stack obsolete; **auth deprecation BANKED
at A+B+C-partial (`b1a92674`)** — removed dead `zero_trust`/`token_manager`/`rbac`
(~1,900 LOC), collapsed authz decorators, dropped stale CSRF entries, fixed 5 pre-existing
desktop tests, corrected the plan (auth_routes/LoginManager/session_manager/API-key branch
are the live desktop-auth keep-path). Remainder (admin user-mgmt routes, MFA, tenant_rls,
`User.role/is_admin/mfa_*` slim) is vestigial-but-wired/cross-cutting → **deferred to the
frontend audit A15/A16**. **Next: A11 `core/axes/`.** Last commit: `a2f26b90`._

This document captures the current working state of the DataLogicEngine desktop
app, the issues fixed in recent sessions, the build/deploy process, and the
known-good verification steps. It is the primary handoff reference; the
`docs/WINDOWS_11_LOCAL_RUNBOOK.md` has the detailed local-run instructions.

> **Audit Plan v2.0 progress (2026-06-11).** Working through
> `docs/audits/DataLogicEngine_Complete_Audit_Plan_v2.md`. Per-session detail
> lives in `REPO_AUDIT_LOG.md`; the live status table is in
> [Section 8](#8-open--next).
>
> | Session | Scope | Commit | Result |
> |---|---|---|---|
> | Sprint 0 | N3 delete legacy axes, N4 Axis 4/5 + honeycomb Axis-3 bug | `821737d1` | ✅ |
> | A4 | `local_model_acceleration/` | `821737d1` | ✅ A4-1/2/3 fixed |
> | A3 | `llm_gateway/` + N2 defense supervisor wired | `1ddeec49` | ✅ |
> | A1a | `truth_core/` + `truth_gate/` | `86486a78` | ✅ A1a-1 fixed |
> | A1b | `truth_memory/` + `truth_link/` | `5027fc3b` | ✅ A3-3/A1a-3 + A4-7 resolved |
> | A2 | `dsqp/` — patent claim | `4390c608` | ✅ matches disclosure; validator process-aware (A2-1) |
> | A2-2 | DSQP LLM-assisted construction | `a1784a17` | ✅ query-derived personas; offline fallback kept |
> | A5 | `dmrf/` — 17-axis router | `5d8dc848` | ✅ all 17 axes; no MLflow conflict; A5-1 wired DMRFDesktopConfig |
> | A6a | `core/simulation/` L1–L5 | `2afe2d14` | ✅ L5 override fixed; 12 dead legacy files removed |
> | A6b | `core/simulation/` L6–L10 + SEKRE | `62aa320f` | ✅ **N1 SEKRE wired**; L6–L10 mapped (no deletions) |
> | **— PHASE 1 COMPLETE (8/8) —** | | | |
> | A7+A8 (Phase 2) | `knowledge_algorithms/` (125 KAs) | `pending` | ✅ 125/125 registry resolve; 117 real + 8 compact + 0 stub; KA-113 + KA-005 + A5-3 fixes |
> | A9 (Phase 2) | `core/persona/quad/` | `pending` | ✅ models/sufficiency/pod_orch/math LIVE (DUP-5 clean); quad_engine demo-only (docstring fixed); A9-1/2/3 forwarded |
> | **A10** | `backend/security/` | — | **NEXT** |
>
> Status correction (recorded Sprint 0): RT-1..RT-18 were already completed
> 2026-06-07/08 (`df29906b`, `0eb2b0bb`, `cc01c15b`; `df29906b` also migrated
> `routes/` → `backend/routes/`) — the v2.0 plan listed them from a stale
> snapshot. Full suite after A6b: **2047 passed / 21 skipped / 0 failed**,
> ruff clean. Both June-10-scan disconnected components are now wired:
> N2 (defense_supervisor, A3) and N1 (SEKRE, A6b).

---

## 1. Current State (2026-05-30)

- Desktop app builds, packages (NSIS), installs, and uninstalls successfully.
- The installer is at the repo root: `DataLogicEngine Setup Latest.exe`.
- Installed per-machine to `C:\Program Files\DataLogicEngine Desktop\`.
- Both provider API keys in `C:\software\DataLogicEngine\API KEY\key.txt` were
  verified valid against the live provider APIs:
  - OpenAI (`sk-proj-…`): valid, 118 models accessible.
  - Gemini (`AQ.Ab8RN6…`): valid, 50 models accessible (works as a Google AI
    Studio key despite the non-`AIza` prefix).
- Uninstall is discoverable via "Uninstall DataLogicEngine" shortcuts on the
  Desktop and Start Menu (created by `frontend/electron/installer.nsh`).

## 2. Root Cause Found This Session (important)

Every earlier "rebuild" only rebuilt the **frontend**. The Python backend bundled
in the installer (`dist/DataLogic_Backend/DataLogic_Backend.exe`) was stale
(built 2026-05-21), so the shipped app ran old backend code regardless of source
fixes. Symptoms this produced:

- `404` for `/api/v1/gateway/dsqp-persona-profiles` and
  `/api/v1/gateway/network-status` (these exist in current source but not the
  old build) — surfaced as the Live Trace `[object Object]` and the System
  Output 404 in the UI.
- The Flask app-context provider fix never took effect → chat failed with
  "No active providers found" / "added to the local offline queue".
- The Settings `size_bytes` guard appeared not to apply.

**Fix:** `frontend/build_installer.ps1` now rebuilds the PyInstaller backend
(`scripts/build_backend.py`) and re-applies the electron-builder npm patch
(`npm run fix:eb`) **before** packaging. The shipped backend now always matches
source.

## 3. Fixes Landed (committed to `main`)

- **Gateway app-context** (`backend/llm_gateway/gateway.py`): `_get_eligible_providers()`
  wraps the `LLMProvider.query` in an explicit `app.app_context()` so provider
  resolution works from async coroutines (Electron-spawned backend).
- **API key forwarding** (`frontend/electron/main.ts`): keys from `.env`
  (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, …) are merged into
  the spawned backend process env.
- **Settings crash** (`frontend/components/settings/DatabaseSettings.tsx`):
  guarded undefined storage-backend metrics with `(metric ?? {})` and optional
  chaining; absent local backends render "0 B / Not created".
- **Provider test errors** (`backend/llm_gateway/api.py` `test_provider`):
  returns specific statuses — `invalid_api_key` (401), `rate_limited` (429),
  `invalid_model` (422), `network_error` (504) — instead of a generic message.
- **Cross-provider failover** already exists in `LLMGateway.process()`: providers
  tried in priority order; auth/`401`/`invalid api key` is non-retryable for that
  provider and triggers failover to the next (e.g. OpenAI → Gemini).
- **Uninstall shortcuts** (`frontend/electron/installer.nsh`): Desktop + Start
  Menu shortcuts created on install, removed on uninstall.
- **Build tooling** (`frontend/scripts/patch-electron-builder.mjs`): durable fix
  for the electron-builder v26 + NVM-for-Windows npm collector failure
  ("No JSON content found in output"). Runs on `postinstall` and before
  `electron:dist`.
- **Unsigned local builds**: `frontend/electron-builder.yml` sets
  `verifyUpdateCodeSignature: false`.

## 4. Environment Notes (Windows dev machine)

- **Two venvs exist:**
  - `.venv311` — Python **3.11.14**, real install. **Use this** for backend
    build and scripts. Has flask, sqlalchemy, cryptography, openai, pyinstaller.
    (Missing `anthropic` — only needed if using the Anthropic provider.)
  - `.venv` — Python 3.13 from the **Windows Store**. Sandboxed; subprocess
    stdout is unreliable. **Avoid for scripting.**
- **Node.js**: NVM-for-Windows at `C:\nvm4w\nodejs` (node.exe + npm).
- **Git**: `C:\Program Files\Git\cmd\git.exe` (not on PATH; call full path).
- Reliable script execution pattern in PowerShell:
  `Start-Process -FilePath <py> -ArgumentList <script> -NoNewWindow -Wait -PassThru`
  with `-RedirectStandardOutput`/`-RedirectStandardError` to files.

## 5. Build & Deploy Process

Full rebuild + repackage (preferred, does everything in order):

```powershell
# Run elevated; rebuilds backend, frontend, patches eb, packages NSIS, copies to root
powershell -ExecutionPolicy Bypass -File frontend\build_installer.ps1
```

Manual steps (if doing piecemeal):

```powershell
# 1. Backend (PyInstaller) — REQUIRED whenever backend source changes
.\.venv311\Scripts\python.exe scripts\build_backend.py
# 2. Frontend
cd frontend
C:\nvm4w\nodejs\node.exe node_modules\next\dist\bin\next build
C:\nvm4w\nodejs\node.exe node_modules\typescript\bin\tsc -p electron
# 3. Patch electron-builder for NVM, then package
node scripts\patch-electron-builder.mjs
C:\nvm4w\nodejs\node.exe node_modules\electron-builder\out\cli\cli.js --win --config electron-builder.yml
```

Before packaging, ensure no `DataLogic_Backend.exe` process is running and that
`frontend\dist\win-unpacked` is removed (stale locked files cause
`ERR_ELECTRON_BUILDER_CANNOT_EXECUTE`).

## 6. Install / Uninstall

- **Install**: run `DataLogicEngine Setup Latest.exe` (elevated). Wizard mode.
- **Uninstall (interactive)**: Desktop or Start Menu "Uninstall DataLogicEngine".
- **Uninstall (silent, blocking)**:
  ```powershell
  $u = 'C:\Program Files\DataLogicEngine Desktop\Uninstall DataLogicEngine Desktop.exe'
  $tmp = Join-Path $env:TEMP 'dle_uninst.exe'; Copy-Item $u $tmp -Force
  Start-Process $tmp -ArgumentList '/S','/allusers','_?=C:\Program Files\DataLogicEngine Desktop' -Verb RunAs -Wait
  ```

## 7. Verification After Install

1. Backend bundled timestamp matches the latest backend build:
   `Get-Item 'C:\Program Files\DataLogicEngine Desktop\resources\backend\DataLogic_Backend.exe'`
2. Launch the app → **Enterprise AI** → send "hello" → expect a real model reply.
3. Open **Settings** → loads without the `size_bytes` crash.
4. **Live Trace** panel shows no `[object Object]`.
5. Live runtime log (for debugging):
   `C:\Users\<user>\AppData\Roaming\DataLogicEngine Desktop\logs\desktop-runtime.log`
   — should NOT show 404s for `/gateway/dsqp-persona-profiles` or
   `/gateway/network-status`.

## 8. Open / Next

### Status (2026-06-11)

- ~~RT-1 multimodal handler bug~~ — done `df29906b`/`0eb2b0bb` (handlers renamed).
- ~~RT-2 unauthenticated `/search/suggest`~~ — done `0eb2b0bb`.
- ~~RT-3..RT-18 routes sprint~~ — all 18 closed; see
  `docs/audits/DataLogicEngine_Routes_Audit.md` resolution table.
- ~~N3 legacy axis files~~ — deleted this session (+ orphaned enums + `__init__.py`).
- ~~N4 Axis 4/5 gap~~ — resolved this session; honeycomb_api Axis-5 lookup bug
  fixed + auth added.
- ~~A4 local_model_acceleration audit~~ — complete; A4-1/2/3 fixed, A4-4/5/7/8
  assigned forward. See `REPO_AUDIT_LOG.md`.

- ~~A3 llm_gateway audit~~ — complete 2026-06-11. Governance enforced
  per-request confirmed; DMRF flag wired; classifier vs KA-113 = different
  axes (model tier vs reasoning tier), by design. Fixed: 4 unauthenticated
  desktop status endpoints (now signed `desktopFetch` + auth), N2 wired,
  A4-4 tier re-probe, A4-5 stream guard, A4-8 `process()` harness.
  Details in `REPO_AUDIT_LOG.md` (A3 entry).
- ~~N2 defense_supervisor~~ — WIRED: `backend/security/defense_supervisor.py`
  screens pipeline queries on the cheapest local Ollama tier (JSON mode,
  8 s timeout, fail-open). Kill switch `DEFENSE_SUPERVISOR_ENABLED=false`.
  Prompt moved to `backend/security/prompts/defense_supervisor.txt`.

- ~~A1a truth_core + truth_gate audit~~ — complete 2026-06-11. Engine is the
  real entry point; L9 max-5 enforced; L10 emergence gate makes real
  decisions; L7 AGI planner real; TruthGate L8 fail-closed. Fixed hardcoded
  `processing_time_ms: 500` in the audit trail. Details in `REPO_AUDIT_LOG.md`
  (A1a entry).

- ~~A1b truth_memory + truth_link audit~~ — complete 2026-06-11 (`5027fc3b`).
  Resolved **A3-3/A1a-3**: confirmed via canonical `dmrf/models.py` `TIER_ORDER`
  that `moderate` = Tier 2; the audit-commit/footer gate wrongly excluded it,
  so Tier 2 runs were skipping audit bundles. Exclusion set normalized to
  `{"", "0", "t0", "1", "t1", "trivial"}` with `.lower().strip()` (also fixes
  the SDK's `"T1"`/`"T2"` casing) across `_build_response`, `_create_trace_run`,
  and the new cache-hit path. Resolved **A4-7**: cache stores/returns
  `original_run_id`; Tier 2+ cache hits now write a `cache_hit` compliance
  `TruthAuditEvent` linking new + original run ids. (Reviewed 2026-06-11: API
  call matches `TruthAuditRecorder.log_event` signature; 127 focused tests pass.)

- ~~A2 dsqp patent-claim audit~~ — complete 2026-06-11. Verdict: matches
  `docs/ip/dsqp_technical_disclosure.md` as the explicitly-scoped deterministic
  slice. 7-step per-axis chain, per-query construction (no cross-query cache),
  registry = question specs, templates = questions only — all confirmed. Fixed
  A2-1 (validator now checks the self-questioning *process* ran, not just
  coverage). Documented A2-2: deterministic answers are axis-keyed scaffolds —
  implement LLM-assisted construction before any external IP filing. Details in
  `REPO_AUDIT_LOG.md` (A2 entry).

- ~~A2-2 DSQP LLM-assisted construction~~ — built 2026-06-11. `dsqp_answer_generator.py`
  generates the 7 persona components from the query on the local model (per-axis
  JSON call), with per-component fallback to the deterministic scaffold; provenance
  + `construction_mode` recorded. `DSQP_LLM_ASSISTED=false` kill switch;
  conftest pins it off for tests. Personas are now genuinely query-derived. Details
  in `REPO_AUDIT_LOG.md` (A2-2 entry).

- ~~A5 dmrf 17-axis router audit~~ — complete 2026-06-11. All 17 axes
  exercised; tier_classifier is the reasoning tier (distinct from the gateway's
  model-escalation classifier); convergence_policy + frost_bridge real; no
  MLflow experiment conflict; 4 adapters real delegations. Fixed A5-1 (wired
  the orphaned `DMRFDesktopConfig`). Forwarded A5-2 (5 overlapping injection
  defenses → A10), A5-3 (unused `ka_controller` param). `REPO_AUDIT_LOG.md`
  (A5 entry).

- ~~A6a core/simulation L1–L5 map~~ — complete 2026-06-11. Live path:
  `SimulationEngine` (app_orchestrator/master_workflow/system_initializer) wires
  L4–L10; master_workflow wires L1–L3. L1–L5 live = layer1_entry / layer2_knowledge
  / layer3_expert / layer4_reasoning / layer5_integration. Fixed A6a-1 (L5
  override). Removed 12 zero-importer dead files (2 dead orchestrators +
  their exclusive layer-variant chains). `REPO_AUDIT_LOG.md` (A6a entry).

- ~~A6b L6–L10 + SEKRE~~ — complete 2026-06-11. Live L6–L10 mapped
  (layer6_enhancement / layer7_agi_system / layer8_quantum / layer9_recursive
  [max-5 enforced] / layer10_synthesis); the 4 variant files are demo/research
  (kept); `legacy_simulation_engine` + `agentic/` live (kept). **N1 SEKRE wired**
  post-L10 in `SimulationEngine` (fail-safe, Tier-3+ gate, read-only default).
  `REPO_AUDIT_LOG.md` (A6b entry).

## ✅ Phase 1 complete — Phase 2 (Reasoning Depth) in progress

- ~~A7 partial — `knowledge_algorithms/` registry/config map + high-risk~~
  done 2026-06-11. All 125 registry entries resolve to importable callables;
  configs are by-convention `config/ka_NN_config.json` (graceful fallback,
  `ka_33` reserved); KA-117 rename confirmed. High-risk KAs verified real
  (KA-014 confidence, KA-061 adversarial fail-closed, KA-005 classification,
  KA-116/032/034/024). **NOTE: the plan's high-risk KA *numbers* were stale**
  (e.g. real `ka_107` = disaster_recovery, not "reasoning boundary"; entropy is
  `ka_116`, not 102) — verify by concept, not the plan's numbering. Fixed A7-1
  (KA-113 length-only → multi-signal). `REPO_AUDIT_LOG.md` (A7 entry).

- ~~A8 per-KA rating sweep + A5-3~~ done 2026-06-11. All 125 KAs rated:
  117 real + 8 compact-real (7 `l10/` modules delegating to `l10/common`, KA-112)
  + 0 stub; 0 orphan configs. A5-3 resolved — KA-005 now emits `suggested_tier`
  (fixing TruthCore's previously-dead KA-005 tiering branch) and the unused
  `DMRFTierClassifier.ka_controller` param was dropped. The 100–117 band are
  *representational* infra KAs (describe ops; the real celery/redis layer
  performs them). `REPO_AUDIT_LOG.md` (A8 entry).

### ✅ A9 — `core/persona/quad/` complete (2026-06-12)

Reachability map done (full detail in `REPO_AUDIT_LOG.md` A9 entry). Verdict:
- **LIVE / canonical:** `models.py` (PersonaProfile 7-component + QueryState),
  `persona_scaling/sufficiency.py` (DUP-5 clean — `GatewayPersonaSufficiencyTool`
  + Phase-5 `PersonaSufficiencyTool`), `persona_scaling/profiles.py`,
  `pod_models.py`, `pod_orchestrator/`, `mathematical_framework/`.
- **DEMO-ONLY:** `quad_engine.py` — heuristic 4-persona engine, importers are demo
  scripts + 1 test only. **Plan premise was wrong**: the real query-time 7-component
  construction is `core/system/persona_construction_service.py` → DSQP, not here.
  Fixed its stale docstring (named the A6a-deleted `layer2_legacy_knowledge.py`).
- **Forwarded carry-overs:** A9-1 `axis_role_mapper.py` (test-only) +
  `persona_loader.py` (script-only) → A29; A9-2 `quad_models.py` (misnamed L3
  models, dup of SDK, 1 script importer) → A14/A29; A9-3 `__init__.py` docstring
  → A31. No risky deletions this session. `tests/persona/quad/` 41 passed.

### A10 — `backend/security/` IN PROGRESS (2026-06-13)

**Major reframe (user-confirmed):** app is now **local-first, single operating mode**;
auth is at the **OS level** (even cloud = single-tenant VM). The multi-user model is
gone. See memory `architecture-single-mode`. This makes a whole sub-stack obsolete.

Carry-overs resolved (REPO_AUDIT_LOG.md A10 entry):
- **A3-4 — ✅ N/A by design** (one owner: `user_role` moot; HONEYPOT→BLOCK correct).
- **A5-2 — ✅ keep all five** injection defenses (defense-in-depth union, distinct
  stages/techniques; still relevant — input protection is independent of user model).
- **SC-2 — ✅ AES-256-GCM is the active data cipher** (`encryption_manager`); Fernet
  only wraps the KEK + legacy fallback. Docs reconciliation remains.
- **Password hashing — ✅ verified 2026-06-12** (werkzeug `scrypt:32768:8:1`); don't re-chase.

**Headline:** multi-user auth/RBAC/session/MFA/tenancy stack is architecturally
obsolete. Desktop single-user auth already works (Windows SID + signed Electron
loopback). `zero_trust.py` + `token_manager.py` are already fully dead (test-only).
Full removal blast radius: **147 auth-decorator usages** + ~29/172 test files.

> **Decision (user, 2026-06-13): plan full deprecation before any code changes.**
> Plan delivered → **`docs/audits/DataLogicEngine_Auth_Deprecation_Plan.md`** (6 phases,
> A–F; Phase A = delete the 2 dead modules, risk-free). **Awaiting review/approval —
> NO auth code changed yet.** Next session: review plan, approve a starting phase.

Other carry-overs: A3-4 + A5-2 (injection-defense consolidation) + SC-2 in A10;
A3-5 in A26; A18-pre in A18. Full list in the plan's carry-over table.

Still open for later sessions:
- A2-2 (future DSQP slice, pre-IP): LLM-assisted answer generation.
- A3-4 (for A10): supervisor `user_role` enrichment; HONEYPOT handling with
  `active_defense.py`.
- ~~A1a-2~~ ✅ done 2026-06-12: `truth_core/router.py` `LLMRouter` dead code removed.
- ~~A1a-4~~ ✅ done 2026-06-12: fabricated "Mock result" fallback → honest
  `skipped`/0.0 (was polluting memory graph + downstream context).

Phase 1 remaining order: A5 → A6a → A6b
- A5: `backend/dmrf/` — 17-axis router, FROST bridge, truth integration adapters

**Still unwired (from June 10 scan):**
- `core/self_evolving/sekre_engine.py` — wire after A6b (layer map first)

### Carry-over from prior sessions

- ~~End-to-end chat~~ — resolved (Section 10). gpt-5.5 returns real replies.
- ~~`anthropic` package~~ — non-issue; provider uses raw `httpx`.
- **Minor:** `RAG context retrieval failed: Access is denied ... llama_index` in
  installed app. Non-fatal; move RAG index dir to per-user runtime dir when needed.
- **Minor:** Gemini/Anthropic providers still use async `httpx`. Apply sync-call
  pattern from Section 10 if either becomes the active chat provider.
- Settings UI: surface `test_provider` status codes inline in `ApiOverlayConfig.tsx`.

## 9. CI Status (2026-05-30 night)

All five originally-failing checks were fixed and pushed to `main`, along with
the chain of jobs that fixing them unmasked (frontend unit tests behind the
typecheck gate; docker-build jobs gated on upstream success). Final result:
**Security Scan, Deploy, and CI/CD Pipeline all green.**

Highlights (full detail in `TODO.md` → "CI And Security Evidence"):
- Dependency scan: the stale `chromadb==0.5.23` pin locked `transformers` onto a
  vulnerable build; bumping `transformers` then exposed that `chromadb 1.x` is in
  the pre-auth CVE range `GHSA-f4j7-r4q5-qw2c` (server-mode only; not reachable
  via the embedded `PersistentClient`). Final pin `chromadb==0.6.3` clears both —
  it is `<1.0.0` and still allows CVE-free `transformers 5.9.0`.
- Bandit B608 `# nosec` on the `sqlite_master` row-count query.
- Frontend typecheck + `LiveTracePanel` unit-test mock fix.
- `verify_docs_references.py` no longer flags absolute API routes (`/api/v1/*`);
  fixed a broken diagram reference in `docs/README.md`.
- npm-audit job deflaked (skip electron binary download).
- Both Dockerfiles copy `frontend/scripts` before `npm ci` (postinstall fix).

## 10. Desktop Chat Enablement (2026-05-31)

End-to-end Enterprise AI chat was failing ("The local desktop queue saved this
request for replay…"). The root cause was a chain of three independent problems,
all now fixed and committed to `main`:

1. **`ukg_sdk` not packaged** (`backend.spec`). The gateway imports its provider
   HTTP clients / overlay from the in-repo SDK via a runtime `sys.path` insert
   that does not exist in the frozen app. The bundled backend logged
   `No module named 'ukg_sdk'`, so `_create_sdk_provider()` returned `None` and
   every request went to the offline queue. Fix: add `sdk/UKG_Python_SDK` to
   `pathex` + `collect_submodules('ukg_sdk')` + `collect_data_files('ukg_sdk')`.
   Also bundled `tiktoken_ext.openai_public` (the `cl100k_base` plugin) so RAG
   token counting stops raising `Unknown encoding cl100k_base`.

2. **gpt-5.5 called incorrectly.** gpt-5.5 is a *reasoning* model: it rejects a
   custom `temperature` and counts reasoning tokens against `max_output_tokens`.
   The provider sent `temperature` and a tiny `max_output_tokens` (the Test Model
   probe sent `5`, below the Responses-API minimum of 16). Fix
   (`ukg_sdk/providers/openai.py`): drop `temperature` for gpt-5.x/o-series, send
   `reasoning={"effort": "medium"}`, and floor `max_output_tokens` to 1024 for
   reasoning models. OpenAI standardized to a **single model, `gpt-5.5`**
   (`model_defaults.py`, `AiModelSettings.tsx`).

3. **Async client vs. Flask's event loop** (the subtle one). Test Model (a single
   isolated call) worked, but the chat runs the multi-step `UKGOverlay` pipeline,
   and Flask runs `async def` views via `asgiref.async_to_sync` on a reused
   thread-local loop. Creating a fresh `AsyncOpenAI` (asyncio/httpx) client per
   call across those steps mismanaged the client lifecycle ("Event loop is
   closed") and every attempt failed. Fix: call the **synchronous** OpenAI client
   (`self.client.responses.create`) — a blocking call has no loop-bound resources
   to mismanage. Validated against the live key: direct call, full
   `UKGOverlay.run`, and two sequential requests via `async_to_sync` all return
   real answers. (Note: the backend does **not** use eventlet — it is not bundled
   and nothing calls `monkey_patch()`; the issue was purely `async_to_sync`.)

**Desktop UI fixes (same session):**
- `ChatInterface.tsx`: replaced mojibaked emoji in the header/avatars (rendered
  as `ðŸŽ¯`/`ðŸ¤–`) with lucide icons (`Target`/`Bot`/`User`).
- `LiveTracePanel.tsx`: error display defensively coerced to a string so it can
  never render `[object Object]`.
- `DesktopStatus.tsx`: the Desktop Engine status panel is now **minimizable** — a
  header `−` collapses it to a small corner pill (click to reopen); the
  preference persists via `lib/state/storage`.
- `NetworkState._configured_providers()` (`gateway.py`): counts active DB
  providers with a saved key, not just `*_API_KEY` env vars, so the desktop
  status reports ONLINE/DEGRADED (not OFFLINE) after a key is saved in Settings.
  (Saving a key never overwrote the other provider — the DB stores one row per
  provider; the moving "Default" badge is just the `is_default` flag.)

**Refactor reverted.** A large, unpushed, in-progress modularization (splitting
`models.py`/routes/`app.py`/tracing into packages) had broken ~19 tests and the
security_scan suite. Since it was local-only, delivered no functional value, and
the chat fix is independent of it, it was reverted with
`git reset --hard origin/main` (recoverable via reflog at `f9c427fc`). All KA
upgrades and the chat fixes are preserved on `main`.

**Verification after installing the latest build:** launch → Enterprise AI → send
"hello" → expect a real gpt-5.5 reply (not the offline-queue message). The
runtime log should show **no** `No module named 'ukg_sdk'` and **no**
`Provider attempt exception`. `network-status` should report
`configured_providers: ["openai", …]` with `state: DEGRADED` (expected on desktop
with no local model) rather than `OFFLINE`.
