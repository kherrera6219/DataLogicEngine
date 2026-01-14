# Testing Guide

> Comprehensive guide for running and maintaining tests in DataLogicEngine

## Overview

DataLogicEngine uses **pytest** as the testing framework with support for:
- Unit tests
- Integration tests
- End-to-end tests
- Coverage reporting
- Async test support

**Current Status:** 56 tests (18 errors to fix)
**Target:** 80%+ code coverage

---

## Quick Start

### Run All Tests

```bash
# Simple run
./scripts/run_tests.sh

# With coverage report
./scripts/run_tests.sh --coverage

# Verbose output
./scripts/run_tests.sh --verbose

# Re-run only failed tests
./scripts/run_tests.sh --failed
```

### Manual Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install test dependencies
pip install pytest pytest-cov pytest-asyncio

# Set test environment
export FLASK_ENV=testing
export DATABASE_URL=sqlite:///test.db

# Run tests
pytest tests/
```

---

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── test_*.py                      # Root-level tests
├── unit/                          # Unit tests
│   ├── test_websocket.py
│   └── ...
├── integration/                   # Integration tests
│   └── ...
├── end_to_end/                    # E2E tests
│   └── test_full_simulation.py
├── axes/                          # 17-Axis framework tests
│   └── test_persona_axes.py
└── utils/                         # Utility tests
    └── test_db_migration_utils.py
```

---

## Writing Tests

### Unit Test Example

```python
# tests/unit/test_example.py
import pytest

def test_example_function():
    """Test description."""
    result = example_function(input_data)
    assert result == expected_value
```

### Integration Test Example

```python
# tests/integration/test_api_endpoints.py
import pytest

def test_knowledge_graph_api(client):
    """Test knowledge graph API endpoint."""
    response = client.get('/api/v1/knowledge/nodes')
    assert response.status_code == 200
    data = response.get_json()
    assert 'nodes' in data
```

### Fixture Example

```python
# tests/conftest.py
import pytest
from app import app as flask_app

@pytest.fixture
def client():
    """Create test client."""
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client
```

---

## Test Categories

### 1. Unit Tests (`tests/unit/`)

Test individual functions and classes in isolation.

**Examples:**
- `test_axis_resolver.py` - Test 17-axis resolution
- `test_knowledge_algorithms.py` - Test individual KAs
- `test_truth_engine.py` - Test truth engine components

**Guidelines:**
- Fast execution (<1s per test)
- No external dependencies
- Mock database/API calls
- Test edge cases

### 2. Integration Tests (`tests/integration/`)

Test component interactions and API endpoints.

**Examples:**
- `test_api_endpoints.py` - Test all REST endpoints
- `test_llm_gateway.py` - Test LLM provider integration
- `test_database_operations.py` - Test ORM operations

**Guidelines:**
- Use test database
- Test realistic workflows
- Verify error handling
- Test authentication/authorization

### 3. End-to-End Tests (`tests/end_to_end/`)

Test complete user workflows.

**Examples:**
- `test_full_simulation.py` - Complete simulation flow
- `test_chat_workflow.py` - Chat request to response
- `test_trace_creation.py` - Trace generation and retrieval

**Guidelines:**
- Test realistic user scenarios
- Include multiple system components
- Verify data persistence
- Test complex state transitions

---

## Common Test Patterns

### Testing API Endpoints

```python
def test_create_node(client, auth_headers):
    """Test node creation endpoint."""
    payload = {
        'name': 'Test Node',
        'type': 'concept',
        'content': 'Test content'
    }
    response = client.post(
        '/api/v1/knowledge/nodes',
        json=payload,
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['id'] is not None
```

### Testing with Database

```python
def test_user_creation(db_session):
    """Test user model creation."""
    user = User(
        username='testuser',
        email='test@example.com'
    )
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.username == 'testuser'
```

### Testing Async Functions

```python
@pytest.mark.asyncio
async def test_async_operation():
    """Test async function."""
    result = await async_function()
    assert result == expected_value
```

### Mocking External Services

```python
from unittest.mock import patch, MagicMock

def test_llm_call(client):
    """Test LLM API call with mock."""
    with patch('openai.ChatCompletion.create') as mock_llm:
        mock_llm.return_value = MagicMock(
            choices=[MagicMock(message={'content': 'Test response'})]
        )

        response = client.post('/api/v1/gateway/chat', json={
            'messages': [{'role': 'user', 'content': 'Test'}]
        })

        assert response.status_code == 200
        mock_llm.assert_called_once()
```

---

## Coverage Requirements

### Target Coverage: 80%+

Run coverage report:

```bash
pytest --cov=backend --cov=core --cov-report=html --cov-report=term
```

View HTML report:

```bash
open htmlcov/index.html
```

### Coverage by Component

| Component | Target | Current | Status |
|-----------|--------|---------|--------|
| Routes | 90% | TBD | 🔴 |
| Truth Engine | 85% | TBD | 🔴 |
| LLM Gateway | 80% | TBD | 🔴 |
| 17-Axis Framework | 80% | TBD | 🔴 |
| Tracing System | 75% | TBD | 🔴 |
| Auth System | 90% | TBD | 🔴 |

---

## Known Test Issues

### Current Failures (18 errors)

To see detailed failures:

```bash
pytest tests/ -v --tb=short
```

### Common Issues

1. **Import Errors**
   - Ensure all dependencies installed: `pip install -r requirements.txt`
   - Check Python path in `conftest.py`

2. **Database Errors**
   - Use test database: `export DATABASE_URL=sqlite:///test.db`
   - Clear test DB before runs: `rm test.db`

3. **Environment Variables**
   - Set `FLASK_ENV=testing`
   - Set all required secrets (even dummy values for tests)

4. **Async Test Failures**
   - Install: `pip install pytest-asyncio`
   - Mark tests: `@pytest.mark.asyncio`

---

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        env:
          FLASK_ENV: testing
          DATABASE_URL: sqlite:///test.db
        run: |
          pytest --cov=backend --cov=core --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## Test Maintenance

### Adding New Tests

1. **Create test file** following naming convention `test_*.py`
2. **Add docstrings** describing what is tested
3. **Use fixtures** for common setup
4. **Follow AAA pattern** (Arrange, Act, Assert)
5. **Run tests** to verify they pass
6. **Check coverage** to ensure adequate coverage

### Test Naming Convention

```python
def test_<function_name>_<scenario>_<expected_result>():
    """Clear description of what this tests."""
    pass

# Examples:
def test_create_node_with_valid_data_returns_201():
    """Test that creating a node with valid data returns 201."""
    pass

def test_create_node_without_auth_returns_401():
    """Test that creating a node without auth returns 401."""
    pass
```

### Before Committing

```bash
# Run all tests
pytest tests/

# Check coverage
pytest --cov=backend --cov=core --cov-report=term

# Run linters
flake8 tests/
black tests/ --check
```

---

## Debugging Tests

### Verbose Output

```bash
pytest tests/ -v
```

### Stop on First Failure

```bash
pytest tests/ -x
```

### Run Specific Test

```bash
pytest tests/test_health_endpoint.py::test_health_endpoint_reports_ok_status
```

### Print Statements

```python
def test_example():
    result = function()
    print(f"Debug: result = {result}")  # Will show with -s flag
    assert result == expected
```

Run with output:
```bash
pytest tests/test_example.py -s
```

### PDB Debugger

```python
def test_example():
    result = function()
    import pdb; pdb.set_trace()  # Breakpoint
    assert result == expected
```

---

## Best Practices

1. **Write tests first** (TDD) when fixing bugs
2. **Keep tests independent** - each test should run in isolation
3. **Use descriptive names** - test names should describe behavior
4. **One assertion per test** - or logically grouped assertions
5. **Test edge cases** - null values, empty lists, boundaries
6. **Mock external services** - don't call real APIs in tests
7. **Clean up after tests** - use fixtures with teardown
8. **Maintain test coverage** - don't let coverage decrease
9. **Run tests before commits** - catch issues early
10. **Review test failures** - don't ignore failing tests

---

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Flask Testing](https://flask.palletsprojects.com/en/latest/testing/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

**Last Updated:** 2026-01-14
**Maintainer:** Development Team
