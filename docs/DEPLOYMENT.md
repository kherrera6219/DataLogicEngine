# Deployment Guide

**Phase**: 39
**Last Updated**: 2026-02-07

## Overview
DataLogicEngine supports two primary deployment targets:
1.  **Desktop (Electron)**: A self-contained `.exe`/`.dmg` with bundled backend.
2.  **Cloud (Docker)**: Containerized Frontend (Next.js Standalone) and Backend (Flask/Gunicorn).

## 1. Desktop Deployment (Windows/Mac)

The desktop build uses `output: 'export'` (Static HTML) served by Electron.

### Build Command
```powershell
# Windows
npm run electron:dist
```
*   **Under the hood**: Runs `cross-env BUILD_MODE=electron npm run build` (generates `out/`) -> Compiles Main Process -> Packages with `electron-builder`.

### Output
*   Artifacts location: `frontend/dist/`
*   Includes: `DataLogicEngine Setup 0.1.0.exe` (Windows)

### Optional WiX/WinSW Path (Windows Service Packaging)

If you are using the WiX manifests under `deploy/windows/`, prepare assets first:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\prepare_wix_assets.ps1
```

This fetches `deploy/windows/winsw.exe` and validates expected backend/frontend WiX inputs.
It also generates dedicated service wrappers:
- `deploy/windows/DataLogic_Backend.exe`
- `deploy/windows/DataLogic_Frontend.exe`

## 2. Cloud Deployment (Docker)

The cloud build uses `output: 'standalone'` (Node.js Server) to support API Rewrites and SSR features.

### Frontend
```bash
cd frontend
docker build -t datalogic-frontend .
```
*   **Note**: Uses default `npm run build` which defaults to `BUILD_MODE=standalone`.
*   **Rewrites**: Configured to proxy `/api/*` to `http://127.0.0.1:5000` (or host networking).

### Backend
```bash
cd backend
docker build -t datalogic-backend .
```
*   **Port**: 5000
*   **Env Vars**: Ensure `.env` is mounted or secrets injected.

### 2.1 GitHub Actions Docker Publish (GHCR)

The deployment workflow at `.github/workflows/deploy.yml` always builds `Dockerfile.cloud` on pushes to `main`.

- Image build: always runs
- Image push to `ghcr.io/<owner>/datalogicengine`: runs only when `GHCR_PAT` is configured
- If `GHCR_PAT` is missing: build still succeeds, push is skipped by design

#### Configure `GHCR_PAT`

1. Create a GitHub Personal Access Token (classic) for the account/org that owns the package.
2. Grant scopes:
   - `write:packages`
   - `read:packages`
   - `delete:packages` (optional, only if cleanup is needed)
3. Add repository secret:
   - Repository `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`
   - Name: `GHCR_PAT`
   - Value: `<your_token>`

#### Expected image tags

The workflow publishes multiple tags through `docker/metadata-action`:
- branch ref tags
- semver tags (when pushing version tags)
- commit SHA tags

#### Quick verification

- Push to `main` and inspect the `Deploy` workflow.
- Confirm `Build Docker Images` completes.
- Confirm package appears under `ghcr.io/<owner>/datalogicengine` if `GHCR_PAT` is set.

## 3. Performance Optimization (Phase 38)

### Frontend Bundle Analysis
To visualize the JS bundle size:
```powershell
$env:ANALYZE="true"; npm run build
```
*   Reports saved to: `frontend/.next/analyze/{client,edge,nodejs}.html`

### Backend Profiling
To profile the Simulation Engine (Async IO + CPU):
```powershell
python scripts/profile_simulation.py
```
*   Generates: `simulation_profile.html` (Flamegraph).

## 4. Troubleshooting

*   **"Static worker exited"**: Usually occurs in `export` mode if a page crashes during rendering. Check `build_error.log`.
*   **Rewrite Issues**: Rewrites work ONLY in Cloud/Standalone mode. Desktop uses direct IPC or absolute URLs.
