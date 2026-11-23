# CR-B0 outbound connection inventory

- Source commit `c18ae6a9c7765c59ab50284166295163b1b764f5`
- Local branch `remediation/phase-b`
- Status **Local discovery recorded. Owner review required before CR-B1.**
- Phase A status **Open**. This local review proceeds under the maintainer's November 13 request. The required Windows status check and formal disposition are still pending.

## Findings requiring disposition

1. Packaged Electron CSP permits image requests to arbitrary HTTPS origins. This is a source-confirmed policy allowance. No renderer request to such an origin was captured. Review rendered image sources and constrain renderer networking alongside backend HTTP. See `frontend/electron/main.ts:1087`.
2. Runtime Sentry can initialize with environment opt-in and a DSN. This path is off by default and would use the configured non-model destination when enabled. The separate CI Sentry probe runs outside the installed process. See `app.py:2086` and `backend/observability/crash_reporting.py:66`.
3. The interactive admin creation script can call the Have I Been Pwned service with a password-derived SHA-1 prefix. Current login and registration route searches found no callers. See `scripts/create_admin_user.py:202` and `backend/security/password_security.py:101`.
4. Additional conditionally callable paths target an update feed, remote MLflow tracking, an OIDC identity provider, legacy external storage, or a blockchain RPC endpoint. Candidate signing and update policy disables the updater. The installed managed storage route rejects arbitrary storage tests. The SSO helpers and blockchain commit entry showed no live route or product call site in the review. Default MLflow tracking is local and the remote path requires the optional dependency and configuration.
5. MCP stdio delegates execution to an approved child process. Its destinations depend on the selected connector. Parent HTTP instrumentation alone cannot observe that traffic. Check child processes and rendered resources when testing the boundary.

## Inventory method

The source review used tracked content for Python imports and network calls (including lazy imports), provider adapters, SDKs, Electron and web fetch and policy sites, subprocess transports, local services, and setup and qualification commands. Source matches were mapped to runtime paths and reviewed for configuration and reachability. The search also considered build and CI network paths, which run outside installed request handling. The report records static reachability and configuration. Runtime packet, DNS, redirect, proxy, packaged-renderer and child-process observations remain pending. No listed destination was contacted for this review.

The plan's original Python expression counts source lines, including comments, in-memory variables, configuration and SDK tests. The appendix retains each match and identifies its disposition. Authlib, the provider SDKs, browser and Electron loads, and subprocesses require checks beyond this expression. Inline references and row line numbers resolve to the source commit above.

Inventory: 142 distinct reviewed source references across 81 files. Network-client import check: 32 import references across 24 files, all covered. Plan expression: 77 matches, all reviewed below.

## Governed providers

| File and line | Library or mechanism | Destination | Governed path and reachability |
| --- | --- | --- | --- |
| backend/llm_gateway/providers/openai.py:32 | OpenAI SDK/HTTP | Configured record endpoint, OPENAI_BASE_URL, or SDK default | Yes — candidate and opted-in fallback |
| backend/llm_gateway/providers/openai.py:69 | OpenAI SDK/HTTP | Same provider endpoint | Yes — completion |
| backend/llm_gateway/providers/openai.py:134 | OpenAI SDK/HTTP | Same provider endpoint | Yes — streaming |
| backend/llm_gateway/providers/google.py:27 | Google Gen AI SDK/HTTP | Google SDK model API default; app manifest has no Google base URL field | Yes — candidate and opted-in fallback |
| backend/llm_gateway/providers/google.py:68 | Google Gen AI SDK/HTTP | Same provider endpoint | Yes — completion |
| backend/llm_gateway/providers/google.py:136 | Google Gen AI SDK/HTTP | Same provider endpoint | Yes — streaming |
| backend/llm_gateway/active_model.py:179 | Provider adapter | Same SDK endpoints; effective provider selected from runtime settings | Conditional — active-model helper; applies where invoked |
| backend/llm_gateway/gateway.py:968 | Provider adapter | Configured or SDK-default model endpoint | Yes — routed provider execution |
| backend/services/local_sentence_embedding.py:94 | Sentence Transformers | Verified local model path | Yes where local semantic retrieval is enabled; source loader requests local files |

## Connectors

| File and line | Library or mechanism | Destination | Governed path and reachability |
| --- | --- | --- | --- |
| core/mcp/mcp_client.py:121 | Subprocess stdio | Owner-configured executable; network destinations are owned by child process | Conditional — explicitly enabled connector; child traffic cannot be inferred from stdio |
| core/mcp/mcp_manager.py:188 | MCP stdio client | Registered connector command and environment | Conditional — connector admission |
| backend/governed_execution/extended_subsystems.py:884 | Injected connector | Connector implementation determines destination | Conditional — authorized external research; result domain checks do not observe transport |

## Desktop and web

| File and line | Library or mechanism | Destination | Governed path and reachability |
| --- | --- | --- | --- |
| frontend/electron/main.ts:782 | Chromium navigation | Loopback dev server; packaged path loads app://-/ | No — shell startup |
| frontend/electron/main.ts:821, 872 | Node fetch | Loopback API at 127.0.0.1:5000 for current callers | No — desktop IPC and lifecycle; multiple occurrences |
| frontend/electron/main.ts:921 | Node fetch | 127.0.0.1:5000 | No — readiness |
| frontend/electron/main.ts:1087 | Chromium CSP | Any HTTPS origin if renderer loads a permitted image | Conditional renderer exposure; no emitted request verified |
| frontend/components/ui/avatar.tsx:39 | Chromium image | Source supplied by caller | No — potential image origin; no remote use observed in reviewed callers |
| frontend/lib/api/client.ts:113, 149, 202, 425, 443, 471 | Browser fetch | NEXT_PUBLIC_API_URL or loopback API default | Client entry path — auth, data calls and retry; not upstream provider transport |
| frontend/app/settings/privacy/page.tsx:26 | Browser fetch | Same configurable API base | No — local-data export |
| frontend/contexts/FeatureFlagContext.tsx:116 | Browser fetch | Same origin | No — management UI |
| frontend/lib/socket.ts:100 | Socket.IO | Caller URL or NEXT_PUBLIC_API_URL; loopback default | Client event transport |
| frontend/next.config.ts:18 | Next.js | Configured CDN, if set at build/runtime as applicable | No — assets; packaged reachability needs observation |
| frontend/next.config.ts:53 | Next.js proxy | Loopback backend | Client entry path for standalone web deployment |
| frontend/proxy.ts:28 | Web CSP | Google Fonts style permission | No — web permission, not a resource request |
| frontend/proxy.ts:44 | Web CSP | Unsplash image and Google Fonts font permissions | No — web permissions, not resource requests |
| backend/security/security_headers.py:98, 99, 101 | Backend web CSP | Third-party CDN and font permissions for browser documents | No — permissions, not a resource request |
| frontend/public/sw.js:42 | Service-worker fetch | Origin of intercepted request | Conditional — if worker is registered; current installed use unverified |

## Other external paths

| File and line | Library or mechanism | Destination | Governed path and reachability |
| --- | --- | --- | --- |
| frontend/electron/main.ts:438, 1781 | electron-updater | DLE_AUTO_UPDATE_FEED_URL | No — startup, scheduled and manual checks; candidate trust policy disables |
| frontend/electron/main.ts:1800 | electron-updater | Configured feed and artifact URLs | No — gated by update state; candidate trust policy disables |
| app.py:2086 | Sentry configuration | SENTRY_DSN if external telemetry opt-in enabled | No — initialization at worker startup |
| backend/observability/crash_reporting.py:66 | Sentry SDK | Configured DSN, including exception and trace transport | Conditional runtime path; opt-in and DSN required; outside approved boundary |
| backend/observability/crash_reporting.py:109 | Sentry SDK | Same DSN | Conditional — application errors with configured SDK |
| backend/dmrf/mlflow_tracker.py:38 | Optional MLflow SDK | Local tracking directory by default; MLFLOW_TRACKING_URI can be remote | Conditional — DMRF recording if optional dependency installed |
| backend/truth_engine/truth_memory/mlflow_tracker.py:37 | Optional MLflow SDK | Local tracking directory by default; MLFLOW_TRACKING_URI can be remote | Conditional — truth-memory recording if optional dependency installed |
| backend/security/password_security.py:101 | requests | api.pwnedpasswords.com | No — called by admin bootstrap script; no normal auth-route use found |
| scripts/create_admin_user.py:202 | Password-security helper | Have I Been Pwned API | No — interactive admin bootstrap branch |
| backend/auth/sso.py:23 | Authlib/OIDC | OIDC_DISCOVERY_URL | No — optional configuration; live login route wiring not found |
| backend/auth/sso.py:35 | Authlib/OIDC | Discovery/document authorization endpoint | No — callable legacy helper, route wiring not found |
| backend/auth/sso.py:40 | Authlib/OIDC | Discovery-defined token/JWKS endpoints | No — callable legacy helper, route wiring not found |
| backend/security/ssrf.py:90 | System DNS | Resolver and validated host name | Conditional helper; no production callers outside module found |
| backend/truth_engine/truth_link/blockchain_adapter.py:58 | Web3 JSON-RPC | BLOCKCHAIN_RPC_URL or loopback 127.0.0.1:8545 | Conditional legacy audit anchoring; no caller from current product entry points found |
| backend/truth_engine/truth_link/blockchain_adapter.py:84 | Web3 JSON-RPC | Configured RPC endpoint | Conditional — connection check if legacy anchoring is invoked |
| backend/truth_engine/truth_link/blockchain_adapter.py:110 | Web3 JSON-RPC | Configured RPC endpoint | Conditional legacy anchor transaction; credentials required |
| backend/truth_engine/truth_memory/commit_service.py:200 | Web3 adapter | Configured blockchain RPC endpoint; existing event loop takes local simulated path | Legacy audit commit helper; only test call sites identified |

## Local data plane and legacy storage

| File and line | Library or mechanism | Destination | Governed path and reachability |
| --- | --- | --- | --- |
| backend/storage/chroma_http.py:391 | httpx | Supervised Chroma HTTP endpoint | Yes — vector operations; direct session sets trust_env=False |
| backend/runtime/podman_data_plane.py:830 | urllib | Supervised Chroma health | No — managed startup/health |
| backend/runtime/podman_data_plane.py:791 | PostgreSQL driver | Supervised PostgreSQL listener | No — managed startup/health |
| backend/runtime/podman_data_plane.py:804 | Redis SDK | Supervised Redis listener | No — managed startup/health |
| backend/runtime/podman_data_plane.py:814 | Neo4j driver | Supervised Bolt listener | No — managed startup/health |
| backend/runtime/podman_data_plane.py:845 | boto3 | Supervised S3-compatible store | No — managed startup/health |
| backend/runtime/podman_data_plane.py:327 | Podman CLI | Locally inspected digest-pinned images | No — catalog references do not prove registry access |
| backend/runtime/podman_data_plane.py:698 | Podman CLI | App-owned internal bridge | No — container network; dynamic host/VM capture remains open |
| backend/runtime/podman_data_plane.py:590 | Podman subprocess | Preflight-verified local image and app-owned network | No — installation-local data plane |
| backend/storage/connection_manager.py:314 | PostgreSQL driver | Runtime-owned PostgreSQL configuration | No — health |
| backend/storage/connection_manager.py:331 | Redis SDK | Runtime-owned Redis configuration | No — health |
| backend/storage/connection_manager.py:346 | Neo4j driver | Runtime-owned Neo4j configuration | No — health |
| backend/storage/connection_manager.py:369 | urllib | Runtime-owned vector host | No — health |
| backend/storage/connection_manager.py:392 | boto3 | Runtime-owned object-store URL | No — health |
| backend/storage/object_store.py:361 | boto3 | Supervised endpoint in managed mode; legacy adapter constructor accepts endpoint | Conditional — object effects if enabled |
| backend/storage/graph_store.py:62 | Neo4j driver | Runtime Bolt URI | Yes — graph retrieval |
| backend/storage/graph_store.py:167 | Redis SDK | Runtime Redis URL | Conditional — graph cache |
| backend/services/rag_service.py:133 | Redis SDK | Runtime Redis URL | Yes — RAG cache where enabled |
| backend/storage/database_manager.py:62 | TCP socket | 127.0.0.1, service port | No — legacy service preflight |
| backend/routes/storage_routes.py:487, 521, 555 | TCP socket | Caller-provided legacy PostgreSQL, Redis or Neo4j host | No — authenticated diagnostic; managed mode rejects before these calls |
| backend/routes/storage_routes.py:611 | Optional Pinecone SDK | Pinecone service via SDK | No — authenticated legacy diagnostic; managed mode rejects |
| backend/routes/storage_routes.py:668 | boto3 | Legacy supplied S3 endpoint or SDK default | No — authenticated legacy diagnostic; managed mode rejects |
| backend/storage/vector_store.py:329 | Optional Pinecone SDK | Cloud vector service via SDK | Legacy class remains; managed factory refuses external vector backends |
| backend/storage/managed_backup.py:622 | Redis, Neo4j, Chroma, S3 and PostgreSQL adapters | App-owned endpoints | No — coordinated export |
| backend/storage/managed_restore.py:90 | Redis, Neo4j, Chroma, S3 and PostgreSQL adapters | Isolated managed recovery instance | No — restore |
| backend/storage/runtime_migrations.py:129 | Redis, Neo4j, Chroma, S3 and PostgreSQL adapters | Supervised and supported migration connections | No — migration |
| backend/storage/runtime_migrations.py:234 | Neo4j driver | Legacy migration source | No — migration only |
| backend/storage/user_deletion.py:577 | Redis, Neo4j, Chroma and other deletion adapters | App-owned endpoints | No — data deletion lifecycle |
| app.py:973 | SQLAlchemy | Configured runtime database; managed PostgreSQL in installed profile | No — health |
| app.py:818 | Redis SDK | Runtime Redis URL | No — cache/health |
| backend/security/compliance_manager.py:265, 316 | SQLAlchemy | Runtime database | Conditional — durable compliance services |
| backend/dmrf/truth_integration/link_adapter.py:49 | Redis SDK | Runtime/adapter-provided Redis URL | Conditional — event bus |
| backend/ingestion/job_coordination.py:38 | Redis SDK | Runtime Redis URL | Conditional — ingestion jobs |
| backend/llm_gateway/admission_limiter.py:75 | Redis SDK | Runtime Redis URL | Yes — governed admission |
| backend/llm_gateway/job_coordination.py:55 | Redis SDK | Runtime Redis URL | Yes — governed async jobs |
| backend/mcp_server/live_state.py:28 | Redis SDK | Runtime Redis URL | Conditional — connector state |
| backend/security/session_manager.py:57 | Redis SDK | Runtime Redis URL | Client authentication/session path |
| backend/simulation/job_coordination.py:36 | Redis SDK | Runtime Redis URL | Conditional — simulation job |
| backend/truth_engine/truth_link/bus.py:171 | Redis SDK | Runtime Redis URL | Conditional — link event bus |
| backend/truth_engine/truth_memory/cache.py:57 | Redis SDK | Runtime Redis URL | Conditional — memory cache |
| backend/knowledge_algorithms/ka_master_controller.py:219 | Celery broker | Runtime Redis or configured worker broker | Conditional — legacy task dispatch |
| backend/observability/support_bundle.py:319 | urllib | Fixed 127.0.0.1:5000 health/ready/metrics | No — support export probes |
| backend/security/security_headers.py:101 | Backend web CSP | Configured document permits Google-hosted fonts and public CDN resources | No — permission only |
| backend/logging_config.py:13 | stdlib socket | No connection at import | No — host metadata |

## Client SDKs

| File and line | Library or mechanism | Destination | Governed path and reachability |
| --- | --- | --- | --- |
| sdk/UKG_Python_SDK/ukg_sdk/api_client.py:185, 286 | httpx | Caller-selected DataLogicEngine base URL | Client-side sync and async API traffic |
| sdk/UKG_Python_SDK/ukg_sdk/client.py:62 | httpx | Caller-selected DataLogicEngine base URL | Client-side API traffic |
| sdk/UKG_Python_SDK/ukg_sdk/dsqp.py:69 | httpx | Caller-selected DataLogicEngine endpoint | Client-side persona API traffic |
| sdk/UKG_Python_SDK/ukg_sdk/overlay.py:94 | httpx | Caller-selected DataLogicEngine base URL or injected client | Client-side governed entry |
| sdk/UKG_Python_SDK/ukg_sdk/audit/postgres.py:36 | asyncpg | Caller DSN | Standalone SDK storage |
| sdk/UKG_Python_SDK/ukg_sdk/memory/postgres.py:38 | asyncpg | Caller DSN | Standalone SDK storage |
| sdk/UKG_Python_SDK/ukg_sdk/memory/redis.py:27 | Redis SDK | Caller URL | Standalone SDK storage |
| sdk/DataLogicEngine_TypeScript_SDK/src/index.ts:211, 518 | fetch | Caller API base or loopback default | Client-side ordinary and streaming traffic |
| examples/gateway/python_openai_compat.py:12 | OpenAI SDK | Caller DATALOGICENGINE_COMPAT_URL or loopback | No — sample client |

## Setup, qualification and CI

| File and line | Library or mechanism | Destination | Governed path and reachability |
| --- | --- | --- | --- |
| scripts/setup_local_databases.py:81 | urllib | EnterpriseDB, GitHub releases, Neo4j and Adoptium | No — legacy/manual provisioning |
| scripts/setup_local_databases.ps1:55, 97, 144 | PowerShell HTTP | EnterpriseDB, GitHub releases and Neo4j | No — legacy/manual provisioning |
| scripts/windows/setup_cache.ps1:32 | PowerShell HTTP | Memurai download service | No — legacy/manual provisioning |
| scripts/windows/setup_db.ps1:70 | PowerShell HTTP | EnterpriseDB download service | No — legacy/manual provisioning |
| scripts/windows/prepare_wix_assets.ps1:27 | PowerShell HTTP | GitHub releases | No — build tooling |
| scripts/windows/start_local_stack.ps1:156 | PowerShell HTTP | Caller-selected local stack preflight URL | No — operator/probe script |
| scripts/windows/run_packaging_smoke.ps1:151 | PowerShell HTTP | Configured readiness endpoint; loopback default | No — qualification only |
| scripts/qualify_object_store_replacement.py:347 | urllib | Fixture object-store endpoint | No — qualification only |
| scripts/qualify_object_store_replacement.py:247 | boto3 | Fixture object-store endpoint | No — qualification only |
| scripts/send_sentry_test_event.py:30 | Sentry SDK | Configured DSN | No — explicit test script and CI job |
| scripts/windows/sign_release_installers.ps1:5 | Signing tooling | DigiCert timestamp service by default | No — signing workflow |
| scripts/setup_ssl_letsencrypt.sh:92, 93, 100, 104 | Certbot/ACME | ACME servers and configured domain | No — web-server provisioning |
| deploy/setup_ssl.sh:36 | Certbot/ACME | ACME servers and configured domain | No — web-server provisioning |
| .github/workflows/deploy.yml:131 | OCI tooling | GitHub Container Registry | No — build/deployment infrastructure |
| .github/workflows/ci.yml:41, 84, 127, 284 | pip | Configured package source | No — test/build environment |
| .github/workflows/security.yml:63 | npm audit | Configured npm registry | No — CI dependency audit |
| .github/workflows/security.yml:283, 285, 287 | Cosign | Signing/identity infrastructure | No — CI signing |
| scripts/verify_internal_data_plane.py:222 | boto3 | App-owned qualification object store | No — verification script |
| scripts/verify_internal_data_plane.py:108, 126 | psycopg2 | App-owned qualification PostgreSQL | No — verification script |
| scripts/runtime_precheck.py:209 | stdlib socket | Local bind preflight | No — verification script |
| scripts/probe_offline_embedding_bundle.py:36 | stdlib socket mock | Synthetic probe blocks socket connection attempts | No — qualification only |

## Plan expression cross-check

| File and line | Disposition |
| --- | --- |
| backend/auth/api_decorators.py:141 | Comment or text reference |
| backend/governed_execution/cancellation.py:1 | Comment or text reference |
| backend/governed_execution/extended_subsystems.py:161 | In-memory requests mapping, local middleware text, or metric label |
| backend/governed_execution/extended_subsystems.py:162 | In-memory requests mapping, local middleware text, or metric label |
| backend/governed_execution/extended_subsystems.py:163 | In-memory requests mapping, local middleware text, or metric label |
| backend/governed_execution/ten_layers.py:1 | Comment or text reference |
| backend/llm_gateway/api.py:403 | In-memory requests mapping, local middleware text, or metric label |
| backend/llm_gateway/latency_metrics.py:2 | In-memory requests mapping, local middleware text, or metric label |
| backend/llm_gateway/latency_metrics.py:81 | In-memory requests mapping, local middleware text, or metric label |
| backend/middleware/__init__.py:145 | Comment or text reference |
| backend/middleware/etag.py:14 | In-memory requests mapping, local middleware text, or metric label |
| backend/observability/support_bundle.py:16 | Covered module — client import, setup, typing, or exception handling |
| backend/observability/support_bundle.py:316 | Covered module — client import, setup, typing, or exception handling |
| backend/observability/support_bundle.py:319 | Reviewed transport or configuration reference |
| backend/routes/auth_routes.py:34 | Comment or text reference |
| backend/runtime/podman_data_plane.py:19 | Covered module — client import, setup, typing, or exception handling |
| backend/runtime/podman_data_plane.py:830 | Reviewed transport or configuration reference |
| backend/security/api_csrf.py:2 | In-memory requests mapping, local middleware text, or metric label |
| backend/security/password_security.py:101 | Reviewed transport or configuration reference |
| backend/security/password_security.py:120 | Covered module — client import, setup, typing, or exception handling |
| backend/security/pii_redaction.py:110 | In-memory requests mapping, local middleware text, or metric label |
| backend/storage/chroma_http.py:362 | Covered module — client import, setup, typing, or exception handling |
| backend/storage/chroma_http.py:363 | Covered module — client import, setup, typing, or exception handling |
| backend/storage/chroma_http.py:364 | Covered module — client import, setup, typing, or exception handling |
| backend/storage/chroma_http.py:392 | Covered module — client import, setup, typing, or exception handling |
| backend/storage/connection_manager.py:18 | Covered module — client import, setup, typing, or exception handling |
| backend/storage/connection_manager.py:369 | Reviewed transport or configuration reference |
| backend/truth_engine/truth_gate/policies.py:35 | In-memory requests mapping, local middleware text, or metric label |
| core/mcp/mcp_client.py:221 | In-memory requests mapping, local middleware text, or metric label |
| core/mcp/mcp_client.py:225 | In-memory requests mapping, local middleware text, or metric label |
| core/mcp/mcp_client.py:302 | In-memory requests mapping, local middleware text, or metric label |
| core/mcp/mcp_client.py:651 | In-memory requests mapping, local middleware text, or metric label |
| core/mcp/mcp_client.py:654 | In-memory requests mapping, local middleware text, or metric label |
| core/mcp/mcp_client.py:683 | In-memory requests mapping, local middleware text, or metric label |
| core/mcp/mcp_client.py:686 | In-memory requests mapping, local middleware text, or metric label |
| core/mcp/runtime_loop.py:12 | Comment or text reference |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:52 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:54 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:58 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:76 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:78 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:89 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:105 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:109 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:111 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:113 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:115 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:116 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:120 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:143 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:147 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:148 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:157 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:167 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:170 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:174 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:180 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:181 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:188 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:197 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:198 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_gateway_client.py:202 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_overlay_run.py:13 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_overlay_run.py:14 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_overlay_run.py:22 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_overlay_run.py:38 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/tests/test_overlay_run.py:39 | SDK test fixture or mock |
| sdk/UKG_Python_SDK/ukg_sdk/api_client.py:90 | Covered module — client import, setup, typing, or exception handling |
| sdk/UKG_Python_SDK/ukg_sdk/api_client.py:140 | Covered module — client import, setup, typing, or exception handling |
| sdk/UKG_Python_SDK/ukg_sdk/api_client.py:200 | Covered module — client import, setup, typing, or exception handling |
| sdk/UKG_Python_SDK/ukg_sdk/api_client.py:240 | Covered module — client import, setup, typing, or exception handling |
| sdk/UKG_Python_SDK/ukg_sdk/api_client.py:301 | Covered module — client import, setup, typing, or exception handling |
| sdk/UKG_Python_SDK/ukg_sdk/client.py:34 | Covered module — client import, setup, typing, or exception handling |
| sdk/UKG_Python_SDK/ukg_sdk/client.py:77 | Covered module — client import, setup, typing, or exception handling |
| sdk/UKG_Python_SDK/ukg_sdk/dsqp.py:69 | Reviewed transport or configuration reference |
| sdk/UKG_Python_SDK/ukg_sdk/overlay.py:28 | Covered module — client import, setup, typing, or exception handling |
| sdk/UKG_Python_SDK/ukg_sdk/overlay.py:88 | Covered module — client import, setup, typing, or exception handling |

## Decision

Discovery coverage checks pass. CR-B1 is paused under the CR-B0 stop condition. Owner disposition is needed for the discovered non-provider paths and their proposed removal, containment or separate handling. The inventory does not establish an enforced allowlist or air-gap support.
