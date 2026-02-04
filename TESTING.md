# Testing Guide

This project maintains a high standard of quality through improved testing practices. This document is the single source of truth for testing standards, workflows, and configuration.

## 📂 Directory Structure

We use a consolidated testing structure:

```text
root/
├── tests/                  # ALL Backend & System tests
│   ├── unit/              # Pure Python unit tests (fast, no I/O)
│   ├── integration/       # API & Database integration tests
│   ├── end_to_end/        # Full system E2E tests
│   └── ...
├── frontend/
│   ├── components/
│   │   └── Foo/
│   │       ├── Foo.tsx
│   │       └── Foo.test.tsx  # Colocated Component Tests (Standard)
│   └── tests/
│       ├── unit/          # Frontend logic/utility tests
│       └── e2e/           # Frontend-specific E2E tests
└── run_test_suite.py       # Master Orchestrator Script
```

## 🚀 Running Tests

### Backend (Python)

We use `pytest`. You can run tests via the master script or directly.

**Master Script (Recommended)**

Runs all phases (Unit -> Integration -> E2E)

```bash
python run_test_suite.py
```

**Direct Execution**

```bash
# Run all
pytest

# Run specific type
pytest tests/unit
pytest tests/integration

# Run specific file
pytest tests/unit/test_user.py
```

### Frontend (Next.js / TypeScript)

We use `vitest` for unit/component tests.

```bash
cd frontend

# Run all tests once
npm test

# Run in watch mode (interactive)
npm run test:watch

# Generate coverage report
npm run test:coverage
```

## ✍️ Writing Tests

### Naming Conventions

- **Files**: Must end in `_test.py` or start with `test_` (Python), or end in `.test.tsx` / `.spec.ts` (JS/TS).
- **Functions**: Must start with `test_` (Python) or `it('should ...')` / `test('...')` (JS/TS).

### Backend Standards

- **Mocking**: Use `unittest.mock` or `pytest-mock`. Avoid hitting real external APIs in `tests/unit`.
- **Fixtures**: reusable fixtures are in `tests/conftest.py`.
- **Markers**: Use `@pytest.mark.asyncio` for async tests.

### Frontend Standards

- **Colocation**: Put component tests right next to the component file.
- **Testing Library**: Use `@testing-library/react` for component interactions.
- **Snapshots**: Use sparingly. Prefer explicit assertions.

## 📊 Coverage Goals

- **Backend**: >70% coverage enforced (matches `pyproject.toml`).
- **Frontend**: >70% coverage enforced.

## 🛠 Troubleshooting

- **Discovery**: If your test isn't running, ensure it starts with `test_` and is in a directory with valid `__init__.py` (if needed) or matching the `testpaths` config.
- **Imports**: We use absolute imports. Ensure your `PYTHONPATH` includes the root directory (handled auto by `pytest`).
