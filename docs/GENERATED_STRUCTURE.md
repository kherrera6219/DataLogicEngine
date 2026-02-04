### backend/
```text
├── .coverage
├── .dockerignore
├── .pylintrc
├── Dockerfile
├── __init__.py
├── admin.py
api/
│   ├── specs/
api_gateway/
auth/
├── celery_app.py
├── chat.py
├── config.py
config/
├── config_manager.py
├── contextual_api.py
core/
├── coverage.json
├── data_loader.py
├── decorators.py
├── email_service.py
├── enterprise_architecture.py
├── export_service.py
├── graphql_schema.py
├── honeycomb_api.py
├── i18n.py
├── init_db.py
knowledge_algorithms/
│   ├── config/
│   ├── l10/
│   ├── l9/
llm_gateway/
├── location_context_engine.py
├── logging_config.py
mcp_server/
│   ├── tools/
├── methods_api.py
middleware/
model_context/
operator/
├── persona_api.py
├── pillar_api.py
quad_persona/
├── regulatory_api.py
reports/
repositories/
├── rest_api.py
├── retention_service.py
routes/
schemas/
├── search_service.py
security/
├── security_api.py
├── security_scan_api.py
├── seed_data.py
services/
simulation/
storage/
├── time_api.py
tracing/
truth_engine/
│   ├── truth_core/
│   ├── truth_gate/
│   ├── truth_link/
│   ├── truth_memory/
├── ukg_api.py
├── ukg_db.py
├── unified_mapping_api.py
utils/
webhook_server/
├── websocket.py
```

### core/
```text
├── __init__.py
algorithms/
axes/
├── coordinate_system.py
data/
engine/
graph/
knowledge_algorithm/
│   ├── implementations/
mcp/
│   ├── servers/
memory/
nlp/
orchestration/
persona/
self_evolving/
simulation/
system/
```

### frontend/
```text
├── .dockerignore
├── .gitignore
.storybook/
├── Dockerfile
├── README.md
app/
│   ├── (auth)/
│   ├── about/
│   ├── admin/
│   ├── algorithms/
│   ├── analytics/
│   ├── chat/
│   ├── dashboard/
│   ├── graph/
│   ├── knowledge/
│   ├── mcp/
│   ├── profile/
│   ├── projects/
│   ├── runs/
│   ├── settings/
│   ├── simulations/
│   ├── truth-engine/
├── build.log
├── build_error.log
├── build_error_2.log
├── build_installer.ps1
├── build_log.txt
├── build_log_5.txt
├── build_log_attempt3.txt
├── build_log_attempt4.txt
├── build_log_deps_fix.txt
├── build_log_final.txt
├── build_log_fix.txt
├── build_log_retry.txt
├── build_output.txt
├── build_report.txt
├── build_standalone_error.log
├── build_verbose.log
├── chat_test_debug.log
├── chat_test_debug_v10.log
├── chat_test_debug_v11.log
├── chat_test_debug_v12.log
├── chat_test_debug_v13.log
├── chat_test_debug_v14.log
├── chat_test_debug_v15.log
├── chat_test_debug_v16.log
├── chat_test_debug_v17.log
├── chat_test_debug_v18.log
├── chat_test_debug_v19.log
├── chat_test_debug_v2.log
├── chat_test_debug_v20.log
├── chat_test_debug_v21.log
├── chat_test_debug_v3.log
├── chat_test_debug_v4.log
├── chat_test_debug_v5.log
├── chat_test_debug_v6.log
├── chat_test_debug_v7.log
├── chat_test_debug_v8.log
├── chat_test_debug_v9.log
components/
│   ├── Chat/
│   ├── Dashboard/
│   ├── Graph/
│   ├── layout/
│   ├── mcp/
│   ├── projects/
│   ├── settings/
│   ├── ui/
contexts/
dist-electron/
├── eb_build.log
├── eb_build_nosign.log
├── eb_error.log
├── electron-builder.yml
electron/
├── eslint.config.mjs
├── frontend_final_coverage.log
├── frontend_test.log
lib/
│   ├── api/
├── lint-results.json
├── lint_final.txt
├── lint_final_v2.txt
├── lint_output.txt
├── lint_output_final.txt
├── lint_output_fresh.txt
├── lint_output_qa.txt
├── lint_output_v2.txt
├── manual_build.log
├── middleware.ts
├── middleware.ts.bak
├── next-env.d.ts
├── next.config.ts
├── nsis_build.log
├── package-lock.json
├── package.json
├── packaging_error.log
├── packaging_error_2.log
├── packaging_error_3.log
├── playwright-electron.config.ts
├── postcss.config.mjs
public/
stories/
│   ├── Chat/
│   ├── Dashboard/
│   ├── Graph/
│   ├── assets/
│   ├── mcp/
│   ├── settings/
storybook-static/
│   ├── sb-common-assets/
│   ├── sb-manager/
│   ├── sb-preview/
├── storybook.log
├── storybook_build_log.txt
├── storybook_build_log_2.txt
├── storybook_debug_3.txt
test-results/
├── test_results.log
tests/
│   ├── unit/
├── tsconfig.json
├── tsconfig.tsbuildinfo
types/
├── ui_coverage_final.log
├── ui_coverage_v2.log
├── ui_coverage_v3.log
├── vitest.config.ts
├── vitest.setup.ts
├── vitest.shims.d.ts
```

### docs/
```text
├── AI_MANAGEMENT_SYSTEM_42001.md
├── API.md
├── API_VERSIONING.md
├── ARCHITECTURE.md
├── CIS_BENCHMARKS.md
├── CONTRIBUTING.md
├── CROSS_USER_TESTING.md
├── DEPLOYMENT.md
├── DEVELOPER_GUIDE.md
├── FILE_STRUCTURE.md
├── K8S_OPERATOR_DESIGN.md
├── MCP_INTEGRATION.md
├── OPERATIONAL_RUNBOOKS.md
├── PRIVACY_POLICY.md
├── PRODUCTION_READINESS.md
├── REACT_NATIVE_RESEARCH.md
├── RELEASE_NOTES_v2.5.0.md
├── SDLC_SSDF_MAPPING.md
├── SECURITY.md
├── SLSA_LEVEL_3_ATTESTATION.md
├── SSL_CONFIGURATION.md
├── STORE_LISTING.md
├── TESTING.md
├── TODO.md
├── WORKFLOW.md
api/
archive/
│   ├── dotnet_service/
│   ├── legacy_chat/
│   ├── obsolete/
│   ├── supporting-documents/
├── openapi.yaml
├── v3_ROADMAP.md
whitepapers/
wireframes/
```

### tests/
```text
├── COMPLETE_TEST_COVERAGE_SUMMARY.md
├── PHASE_2_SUMMARY.md
├── TEST_IMPROVEMENTS_SUMMARY.md
axes/
compliance/
├── conftest.py
contract/
end_to_end/
integration/
integration_routes/
knowledge_algorithms/
performance/
quad_persona/
security/
simulation/
├── test_app_security.py
├── test_config.py
├── test_critical_fixes.py
├── test_db_migration.py
├── test_e2e_phases.py
├── test_final_assembly.py
├── test_hardening_assembly.py
├── test_health_endpoint.py
├── test_logging_config.py
├── test_password_policy.py
├── test_production_fidelity.py
├── test_security_hardening.py
├── test_simulation_stack.py
├── test_unified_services.py
truth_engine/
unit/
utils/
├── verify_consensus_v2.py
├── verify_federated_sync_v2.py
├── verify_ml_routing_v2.py
windows/
```
