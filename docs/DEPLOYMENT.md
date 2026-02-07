# Deployment Guide

**Phase**: 39
**Last Updated**: 2026-01-29

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
