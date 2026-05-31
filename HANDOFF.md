# DataLogicEngine — Session Handoff

_Last updated: 2026-05-30 (afternoon session)_

This document captures the current working state of the DataLogicEngine desktop
app, the issues fixed in recent sessions, the build/deploy process, and the
known-good verification steps. It is the primary handoff reference; the
`docs/WINDOWS_11_LOCAL_RUNBOOK.md` has the detailed local-run instructions.

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

- Confirm end-to-end chat success on the freshly installed build (user to verify).
- ~~`anthropic` package not installed in `.venv311`~~ — **resolved (non-issue):**
  the Anthropic provider (`sdk/UKG_Python_SDK/ukg_sdk/providers/anthropic.py`)
  calls the Messages API over raw `httpx` and needs no `anthropic` SDK package.
- Consider surfacing the new `test_provider` status codes in the Settings UI so
  an invalid key shows "Invalid API key" inline (`ApiOverlayConfig.tsx`).

## 9. CI Status (2026-05-30 evening)

All five previously-failing checks were fixed and pushed to `main` (commits
`01db1724`, `b1e48c97`): Code Security Scan, Dependency Security Scan, CI/CD
`backend-test`, CI/CD `frontend-build`, and Deploy `Build and Test`. Root cause
of the dependency-scan failure was a stale `chromadb==0.5.23` pin that locked the
transitive `transformers` onto a vulnerable build; aligned to the validated
`chromadb==1.4.1`, resolving to CVE-free `transformers 5.9.0`. See `TODO.md` →
"CI And Security Evidence" for details.
