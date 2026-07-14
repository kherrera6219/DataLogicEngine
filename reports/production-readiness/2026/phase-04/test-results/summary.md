# Phase 4 Test Results

| Suite | Result |
|---|---|
| Focused migrations/storage/packaging/routes/unit set | 137 passed |
| Complete backend regression | 1,880 passed, 18 skipped after Chroma advisory mitigation |
| Complete frontend Vitest regression | 81 files, 402 tests passed |
| Ruff | Passed |
| Frontend ESLint | Passed with one pre-existing test warning |
| Frontend type check | Passed |
| Electron TypeScript build | Passed |
| Next.js production build | Passed |
| Documentation references | Passed after evidence dossier creation |
| Trust-boundary gates | 426 routes classified, zero public-error/secret findings, fresh 19-channel Electron gate passed |
| Chroma advisory mitigation | 5 focused security tests passed; locked Rust server and constrained client contract verified |

The live five-service qualification is recorded separately in
`phase04_data_lifecycle_qualification.json`.
