# Contributing to DataLogicEngine

## Document control

| Field | Value |
|---|---|
| Document ID | DLE-ROOT-004 |
| Title | Contribution controls |
| Document version | v1.1.0 |
| Product version | 4.4.0 |
| Status | active |
| Audience | Contributors, maintainers, and reviewers |
| Owner | Platform Engineering |
| Approver | Kevin Herrera, Product Owner |
| Source of authority | Repository governance, branch protections, and required validation workflows |
| Confidentiality | Public |
| Last reviewed | 2026-07-14 |
| Next-review trigger | Contribution workflow, toolchain, branch, or validation-gate change |
| Requirements and evidence | CI workflows, root plan, and `docs/DEVELOPER_GUIDE.md` |

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Prerequisites](#prerequisites)
3. [Getting Started](#getting-started)
4. [Development Setup](#development-setup)
5. [Contribution Workflow](#contribution-workflow)
6. [Coding Standards](#coding-standards)
7. [Security Requirements](#security-requirements)
8. [Commit Guidelines](#commit-guidelines)
9. [Pull Request Process](#pull-request-process)
10. [Testing Requirements](#testing-requirements)
11. [Documentation Standards](#documentation-standards)
12. [Branch Naming Conventions](#branch-naming-conventions)
13. [Getting Help](#getting-help)
14. [License Agreement](#license-agreement)

---

## Code of Conduct

All contributors are expected to uphold our community standards. Please read [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) before contributing. Violations may be reported to [conduct@datalogicengine.com](mailto:conduct@datalogicengine.com).

---

## Prerequisites

Before contributing, ensure you have the following installed and configured:

| Requirement | Minimum Version | Notes |
|-------------|----------------|-------|
| Python | 3.11 | 3.12+ supported |
| Node.js | 24.x | Required for frontend and tooling |
| PostgreSQL | 15+ | Required for integration tests (docker dev default is `postgres:15`; the native local stack installs 16) |
| Git | 2.40+ | |

For documentation standards, see:

- [`docs/SOFTWARE_LIFECYCLE_PLAN.md`](docs/SOFTWARE_LIFECYCLE_PLAN.md)
- [`docs/REQUIREMENTS_TRACEABILITY.md`](docs/REQUIREMENTS_TRACEABILITY.md)

---

## Getting Started

### Finding Work to Contribute

1. Browse the [Issues](https://github.com/kherrera6219/DataLogicEngine/issues) page for open items.
2. Filter by `good first issue` for onboarding-friendly tasks, or `help wanted` for higher-priority items.
3. Comment on the issue to indicate your intent before starting work.
4. For major changes (new features, architectural refactors), open an issue for discussion **before** writing code.

### Contribution Size Guidelines

| Change Type | Process |
|-------------|---------|
| Typos, documentation fixes | Submit a PR directly |
| Bug fixes, minor features | Create an issue first, then submit PR |
| New features, refactoring, API changes | Open a discussion issue; wait for maintainer acknowledgment before starting |

---

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/<your-username>/DataLogicEngine.git
cd DataLogicEngine
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.template .env
# Edit .env and set SESSION_SECRET and at least one AI provider key
```

### 3. Install Dependencies

```bash
# Python dependencies
python -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

# Node.js dependencies (frontend + Electron)
cd frontend
npm install
cd ..
```

### 4. Enable Pre-commit Hooks

```bash
git config core.hooksPath .githooks
```

This enforces lint and type checking before each commit, consistent with the CI gate.

### 5. Start Development Servers

```bash
# Terminal 1 — Backend (canonical entry: applies runtime compat patches
# and manages the local database lifecycle; FLASK_ENV enables debug)
FLASK_ENV=development python main.py

# Terminal 2 — Frontend
cd frontend && npm run dev
```

> **Windows:** Use the managed startup script instead:
> ```powershell
> powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_local_stack.ps1
> ```

---

## Contribution Workflow

```
1. Sync fork with upstream main
2. Create a feature branch (see Branch Naming Conventions)
3. Implement changes following Coding Standards
4. Write or update tests to cover changes
5. Run the full test suite and verify all checks pass
6. Update relevant documentation
7. Add an entry to CHANGELOG.md under "Unreleased"
8. Push branch and open a Pull Request
9. Respond to reviewer feedback
10. Maintainer merges after approval
```

### Sync with Upstream

```bash
git checkout main
git fetch upstream
git merge upstream/main
```

---

## Coding Standards

### Python

This project follows [PEP 8](https://peps.python.org/pep-0008/) with the following project-specific rules:

| Rule | Value |
|------|-------|
| Maximum line length | 100 characters |
| Class naming | `PascalCase` |
| Function/variable naming | `snake_case` |
| Constant naming | `UPPER_SNAKE_CASE` |
| Type hints | Required on all public functions |
| Docstrings | Google-style on all public functions and classes |
| Linting | `ruff check . --select E9,F63,F7` — must pass the CI blocking rule set |

**Example — Compliant Python function:**

```python
def calculate_knowledge_score(node_id: str, context: dict) -> float:
    """Calculate the knowledge score for a given node.

    Args:
        node_id: Unique identifier for the knowledge graph node.
        context: Context dictionary containing relevant metadata.

    Returns:
        Float representing the computed knowledge score (0.0–1.0).

    Raises:
        ValueError: If node_id is empty or None.
    """
    if not node_id:
        raise ValueError("node_id cannot be empty")

    score = 0.0
    # Implementation
    return score
```

### TypeScript / React

This project follows the [Airbnb JavaScript Style Guide](https://airbnb.io/javascript/) with TypeScript strict mode enabled.

| Rule | Value |
|------|-------|
| Language | TypeScript (strict mode) |
| Component naming | `PascalCase` |
| Hook naming | `useFeatureName` |
| Component style | Functional components with hooks |
| Data fetching | SWR with explicit loading and error states |
| Styling | Tailwind CSS utility classes |
| Linting | ESLint — must pass with zero errors |
| Type checking | `npm run typecheck` — must pass |

**Example — Compliant React component:**

```tsx
interface KnowledgeNodeProps {
  nodeId: string;
  data: { label: string };
  onSelect: (id: string) => void;
}

const KnowledgeNode: React.FC<KnowledgeNodeProps> = ({ nodeId, data, onSelect }) => {
  const [isSelected, setIsSelected] = useState(false);

  const handleClick = useCallback(() => {
    setIsSelected(true);
    onSelect(nodeId);
  }, [nodeId, onSelect]);

  return (
    <div
      className={isSelected ? 'node-selected' : 'node'}
      onClick={handleClick}
      role="button"
      tabIndex={0}
    >
      {data.label}
    </div>
  );
};

export default KnowledgeNode;
```

### File Structure Conventions

**Python backend services:**

```
backend/
  service_name/
    __init__.py
    routes.py       # API endpoint handlers
    models.py       # SQLAlchemy models
    services.py     # Business logic
    utils.py        # Helper utilities
```

**React frontend components:**

```
components/
  FeatureName/
    index.tsx
    FeatureName.module.css
    FeatureName.test.tsx
```

---

## Security Requirements

All contributions must comply with the enterprise hardening architecture. Non-compliant submissions will be rejected in code review.

| Requirement | Detail |
|-------------|--------|
| **PII Protection** | Any model field containing PII must use `EncryptionManager` field-level encryption (AES-256-GCM) |
| **Access Control** | DataLogicEngine is single-owner / local-first. Authenticated routes use `@api_login_required` (or `@login_required`); owner-only endpoints add a `current_user_is_owner()` check. There is no multi-user RBAC/roles/permissions. |
| **Input Validation** | All inputs must be validated using Pydantic models or Marshmallow schemas |
| **No Hardcoded Secrets** | No hardcoded credentials, tokens, or "TODO security" stubs |
| **Desktop Auth** | New authentication flows must respect the single-owner desktop auto-login model (OS-level identity). There is no multi-user login, MFA/TOTP, or SSO/OIDC. |

**Secure coding examples:**

```python
# Input validation — use schema validation
from marshmallow import Schema, fields, validate

class NodeSchema(Schema):
    label = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    node_type = fields.Str(validate=validate.OneOf(['knowledge', 'sector', 'regulatory']))

# Database queries — always parameterized
from sqlalchemy import text

query = text("SELECT * FROM nodes WHERE id = :node_id")
result = db.session.execute(query, {"node_id": node_id})

# Route protection — single-owner desktop auth (no multi-user RBAC)
from flask import abort
from flask_login import current_user
from backend.auth.api_decorators import api_login_required, current_user_is_owner

@app.route('/api/nodes')
@api_login_required
def list_nodes():
    # owner-only endpoints add an explicit ownership check
    if not (current_user.is_authenticated and current_user_is_owner()):
        abort(403)
    ...
```

---

## Commit Guidelines

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

### Commit Types

| Type | Usage |
|------|-------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `docs` | Documentation changes only |
| `style` | Formatting changes (no logic change) |
| `refactor` | Code restructuring without behavior change |
| `test` | Adding or updating tests |
| `chore` | Maintenance, dependency updates |
| `perf` | Performance improvements |

### Rules

- Use present tense: "add feature" not "added feature"
- Use imperative mood: "fix bug" not "fixes bug"
- Keep subject line under 72 characters
- Reference issues in the footer: `Closes #123`

### Examples

```bash
feat(knowledge-graph): add multi-hop node filtering
fix(auth): resolve JWT expiration race condition on token refresh
docs(api): document rate limit headers in API reference
test(mcp): add OAuth scope enforcement contract tests
chore(deps): upgrade Flask to 3.1.2 and SQLAlchemy to 2.0.46
```

---

## Pull Request Process

### Pre-submission Checklist

Before opening a PR, verify all of the following pass locally:

```bash
# Python linting (must have zero findings)
.venv/bin/python -m ruff check . --select E9,F63,F7

# Python tests with coverage
python -m pytest tests/ --cov=core --cov=backend -v

# Frontend type checking (must pass with zero errors)
npm --prefix frontend run typecheck

# Frontend lint
npm --prefix frontend run lint

# Environment parity check
python scripts/verify_environment_parity.py

# Lockfile integrity check
python scripts/verify_lockfiles.py
```

Additionally:

- [ ] All existing tests pass
- [ ] New tests added for new functionality or bug fixes
- [ ] Relevant documentation updated (README, API docs, docstrings)
- [ ] `CHANGELOG.md` updated under the `Unreleased` section
- [ ] No hardcoded secrets, credentials, or debug flags committed

### Pull Request Template

When opening a PR, complete the full template:

```markdown
## Summary
Brief description of what this PR changes and why.

## Type of Change
- [ ] Bug fix (non-breaking change resolving an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature that changes existing behavior)
- [ ] Documentation update

## Testing
- [ ] Unit tests added or updated
- [ ] Integration tests added or updated
- [ ] Manual testing completed — describe steps taken
- [ ] All CI checks pass

## Security Checklist
- [ ] No hardcoded secrets or credentials
- [ ] Input validation applied to all user-facing inputs
- [ ] Single-owner desktop auth enforced (`@api_login_required` / `current_user_is_owner()` where applicable)
- [ ] No new SQL injection, XSS, or SSRF vectors introduced

## Documentation
- [ ] Docstrings updated for modified functions and classes
- [ ] API documentation updated (if applicable)
- [ ] Architecture documentation updated (if applicable)
- [ ] README updated (if applicable)

## Related Issues
Closes #<issue-number>
```

### Review and Merge Process

1. **Automated CI gate:** All workflows in `.github/workflows/` must pass (lint, tests, security scan, schema parity).
2. **Code review:** At least one maintainer approval is required.
3. **Revision:** Address all requested changes before re-requesting review.
4. **Merge:** Maintainers merge approved PRs via squash merge to maintain a clean commit history.

---

## Testing Requirements

### Test Coverage Minimums

| Module | Minimum Coverage |
|--------|-----------------|
| `core/` | 80% |
| `backend/security/` | 80% |
| `backend/` (all other) | 70% |

### Writing Tests

**Python test example (pytest):**

```python
import pytest
from core.knowledge_graph import KnowledgeGraph

class TestKnowledgeGraph:
    @pytest.fixture
    def graph(self):
        return KnowledgeGraph()

    def test_add_node_returns_valid_id(self, graph):
        node_id = graph.add_node("knowledge", {"label": "Test Node"})
        assert node_id is not None

    def test_add_node_persists_label(self, graph):
        node_id = graph.add_node("knowledge", {"label": "Test Node"})
        assert graph.get_node(node_id)["label"] == "Test Node"

    def test_add_node_raises_on_empty_type(self, graph):
        with pytest.raises(ValueError):
            graph.add_node("", {"label": "Test"})
```

**TypeScript test example (Vitest):**

```tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import KnowledgeNode from '../components/KnowledgeNode';

describe('KnowledgeNode', () => {
  it('renders the node label', () => {
    render(<KnowledgeNode nodeId="1" data={{ label: 'Test Node' }} onSelect={vi.fn()} />);
    expect(screen.getByText('Test Node')).toBeInTheDocument();
  });

  it('calls onSelect with nodeId when clicked', async () => {
    const onSelect = vi.fn();
    render(<KnowledgeNode nodeId="42" data={{ label: 'Node' }} onSelect={onSelect} />);
    await screen.getByRole('button').click();
    expect(onSelect).toHaveBeenCalledWith('42');
  });
});
```

### Running Tests

```bash
# Python unit tests
python -m pytest tests/ -v

# Python with coverage report
python -m pytest --cov=core --cov=backend --cov-report=html tests/

# JavaScript unit tests
cd frontend && npm test

# JavaScript with coverage
cd frontend && npm test -- --coverage

# E2E tests (Playwright)
cd frontend && npm run test:e2e
```

---

## Documentation Standards

| Code Type | Standard |
|-----------|----------|
| Python | Google-style docstrings on all public classes and functions |
| TypeScript | JSDoc comments on exported interfaces and functions |
| Complex logic | Inline comments explaining *why*, not *what* |

When adding features, update the following as applicable:

- `README.md` — if the change affects setup, usage, or capabilities
- `docs/INTERFACE_INTEGRATION.md` — for any new or modified API endpoints
- `docs/ARCHITECTURE.md` — for architectural or structural changes
- `CHANGELOG.md` — always, under the `Unreleased` section
- Inline docstrings — always

Full documentation governance is defined in [`docs/SOFTWARE_LIFECYCLE_PLAN.md`](docs/SOFTWARE_LIFECYCLE_PLAN.md).

---

## Branch Naming Conventions

| Prefix | Use |
|--------|-----|
| `feature/` | New features or capabilities |
| `fix/` | Bug fixes |
| `docs/` | Documentation-only updates |
| `refactor/` | Code restructuring without behavior change |
| `test/` | New or updated tests only |
| `chore/` | Dependency updates, tooling, CI changes |

**Examples:**

```
feature/knowledge-graph-node-filtering
fix/jwt-expiration-race-condition
docs/api-rate-limit-headers
test/mcp-oauth-scope-enforcement
```

---

## Getting Help

| Channel | Purpose |
|---------|---------|
| [GitHub Issues](https://github.com/kherrera6219/DataLogicEngine/issues) | Bug reports |
| [GitHub Discussions](https://github.com/kherrera6219/DataLogicEngine/discussions) | Questions, ideas, design discussions |
| [Security Reports](mailto:security@datalogicengine.com) | Responsible vulnerability disclosure |

---

## License Agreement

By submitting a contribution to this repository, you agree that your work will be licensed under the same terms as the project: the **PolyForm Noncommercial License 1.0.0**. See [`LICENSE`](LICENSE) for full terms.

---

*Thank you for contributing to DataLogicEngine.*
