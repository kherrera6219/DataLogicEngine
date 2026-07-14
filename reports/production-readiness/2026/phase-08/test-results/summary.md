# Phase 8 Test Results

Date: 2026-07-13

| Gate | Result |
|---|---|
| Full backend | 1,993 passed, 18 skipped, 21 warnings; 109.83 seconds |
| Full frontend | 403 passed across 82 files |
| Frontend typecheck | Passed |
| Frontend lint | Passed; zero errors, one pre-existing warning |
| Frontend production build | Passed; 30 static pages generated |
| Python SDK | 30 passed |
| TypeScript SDK | 5 passed; build passed |
| Contract suite | 22 passed, 1 skipped |
| OpenAPI compatibility diff | Passed |
| Migration suite | 18 passed; 21 revisions; head `b7c8d9e0f1a2` |
| Gateway/auth/scope/schema/admission/idempotency | Passed |
| Async/result/cancel/restart/object-storage coordination | Passed |
| Trace ownership/evidence authorization | Passed |
| Ruff | Passed |
| Python compilation | Passed |
| Documentation references | Passed with zero errors |
| Diff whitespace | Passed |

Backend warnings are retained SQLAlchemy legacy API, Python locale deprecation,
MCP AsyncMock test cleanup, and Flask-Session signer deprecation warnings. They
did not fail the Phase 8 checkpoint and remain visible for later cleanup. The
frontend warning is the pre-existing unused `onOpenChange` test parameter in
`ConfirmationDialog.test.tsx`.
