# Development Guide

## Purpose

This file is the quick-entry development guide for contributors working in the repository root. It complements the deeper material in [`CONTRIBUTING.md`](CONTRIBUTING.md), [`TESTING.md`](TESTING.md), and [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md).

## Prerequisites

- Python 3.11+
- Node.js 24+
- npm 11+
- Git 2.40+
- Optional local services for full-stack work: PostgreSQL, Redis, Neo4j, MinIO

## Initial setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.template .env
git config core.hooksPath .githooks

cd frontend
npm ci
cd ..
```

## Recommended preflight

Run the local environment doctor before first boot or when onboarding a new machine:

```bash
python scripts/dev_doctor.py --skip-ports
```

## Running the application

### Backend

```bash
flask db upgrade
python main.py
```

`AUTO_CREATE_SCHEMA=true` is available only as a local escape hatch for disposable databases. The default Phase 2 startup path expects migrations.

### Frontend

```bash
cd frontend
npm run dev
```

### Windows local stack

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1
```

## High-value development commands

### Frontend quality

```bash
cd frontend
npm run lint
npm run typecheck
npm test
```

### Backend quality

```bash
pytest tests --maxfail=20
```

### Documentation and governance

```bash
python scripts/dev_doctor.py --skip-ports
python scripts/verify_environment_parity.py
python scripts/verify_lockfiles.py
python scripts/verify_docs_references.py
```

## Working agreements

- Prefer targeted, incremental changes over broad rewrites.
- Update documentation in the same change when behavior, setup, or governance changes.
- Keep tests aligned with actual API contracts.
- Do not commit secrets, `.env` contents, or generated credentials.
- Use existing scripts in `scripts/` and `scripts/windows/` before inventing new setup flows.

## Where to go next

- Architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- Testing: [`docs/TESTING.md`](docs/TESTING.md)
- Deployment: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
- Contributing policy: [`CONTRIBUTING.md`](CONTRIBUTING.md)
