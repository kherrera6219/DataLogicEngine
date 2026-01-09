# Contributing to DataLogicEngine

Thank you for your interest in contributing to the Universal Knowledge Graph! We follow strict enterprise standards to ensure code quality, security, and maintainability.

## 1. Development Workflow

### Branching Strategy

- **main**: Production-ready code.
- **dev**: Integration branch for new features.
- **feature/<name>**: Feature branches (e.g., `feature/graph-viz`).
- **bugfix/<name>**: Bug fix branches (e.g., `bugfix/auth-timeout`).

### Commits

- Use Conventional Commits: `feat: add new axis`, `fix: resolve race condition`.
- Sign all commits (GPG).

---

## 2. Code Standards

### Backend (Python/Flask)

- **Style**: PEP 8.
- **Type Hints**: Required for all function signatures.
- **Documentation**: Docstrings for every module, class, and function.
- **Error Handling**: Use custom exceptions in `backend/exceptions.py`. No bare `except:` clauses.

### Frontend (Next.js/TypeScript)

- **Style**: ESLint + Prettier (Standard Config).
- **Components**: Use shadcn/ui components from `components/ui`.
- **State**: Use React Server Components where possible; `useParams` / `useSearchParams` for route state.
- **Types**: Strict TypeScript mode. No `any`.

---

## 3. Pull Request Process

1.  **Tests**: Ensure all unit tests pass (`pytest` / `npm run test`).
2.  **Linting**: Run linters locally before pushing.
3.  **Review**: At least one approval required from a code owner.
4.  **CI**: All CI checks must pass.

## 4. Documentation

- Update `docs/API.md` if you modify endpoints.
- Update `README.md` if you change environment setup.
- Add architectural decisions to `docs/ARCHITECTURE.md`.
