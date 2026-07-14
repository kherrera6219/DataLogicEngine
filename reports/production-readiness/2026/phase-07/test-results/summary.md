# Phase 7 Test Results

Date: 2026-07-13

| Gate | Result |
|---|---|
| Full backend | 1,945 passed, 18 skipped, 21 warnings; 98.36 seconds |
| Full frontend | 402 passed across 81 files |
| Frontend typecheck | Passed |
| Frontend lint | Passed; zero errors, one pre-existing warning |
| Frontend production build | Passed; 30 static pages generated |
| SDK | 25 passed |
| Corrected backend API/migration expectations | 5 passed |
| Corrected frontend provider-copy/settings expectations | 11 passed |
| Ruff | Passed |
| Python compilation | Passed |
| Provider manifest check | Passed |
| Migration head | `d3e4f5a6b7c8` |
| Secret storage | Passed; zero findings |
| Public error contract | Passed; 397 files, zero findings |
| Schema parity | Passed; zero errors/warnings |
| Lockfile governance | Passed |
| Documentation references | Passed with zero errors |
| Diff whitespace | Passed |

Warnings retained from the full backend suite are known SQLAlchemy legacy API,
Python locale deprecation, MCP AsyncMock test cleanup, and Flask-Session signer
deprecation warnings. They did not fail the Phase 7 checkpoint and remain visible
for later cleanup. The one frontend warning is the pre-existing unused
`onOpenChange` test parameter in `ConfirmationDialog.test.tsx`.
