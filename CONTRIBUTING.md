# Contributing to DataLogicEngine

Thank you for your interest in contributing to DataLogicEngine! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Node.js 20.x or higher
- PostgreSQL 16
- Git
- Basic understanding of Flask and Next.js

### Finding Issues to Work On

1. Check the [Issues](https://github.com/kherrera6219/DataLogicEngine/issues) page
2. Look for issues labeled `good first issue` or `help wanted`
3. Comment on the issue to let others know you're working on it
4. Wait for maintainer approval before starting major changes

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/DataLogicEngine.git
   cd DataLogicEngine
   ```

2. **Set up your development environment**
   ```bash
   # Copy environment template
   cp .env.template .env

   # Install Python dependencies
   pip install -r requirements-enterprise.txt

   # Install Node.js dependencies
   npm install

   # Initialize the database
   python init_db.py
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Start the development servers**
   ```bash
   # Terminal 1 - Backend
   gunicorn --bind 0.0.0.0:5000 main:app --reload

   # Terminal 2 - Frontend
   npm run dev
   ```

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/kherrera6219/DataLogicEngine/issues)
2. If not, create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment details (OS, Python version, Node version)
   - Screenshots if applicable

### Suggesting Enhancements

1. Check existing issues and discussions
2. Create a new issue with:
   - Clear description of the enhancement
   - Use cases and benefits
   - Potential implementation approach
   - Any relevant examples or mockups

### Code Contributions

1. **Small Changes** (typos, documentation): Submit a PR directly
2. **Medium Changes** (bug fixes, minor features): Create an issue first
3. **Large Changes** (new features, refactoring): Discuss in an issue before starting

## Coding Standards

### Python Code

Follow PEP 8 style guidelines:

```python
# Good
def calculate_knowledge_score(node_id: str, context: dict) -> float:
    """Calculate the knowledge score for a given node.

    Args:
        node_id: Unique identifier for the node
        context: Context dictionary with relevant metadata

    Returns:
        Float representing the knowledge score
    """
    if not node_id:
        raise ValueError("node_id cannot be empty")

    score = 0.0
    # Implementation
    return score
```

**Guidelines:**
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Maximum line length: 100 characters
- Use meaningful variable names
- Follow naming conventions:
  - Classes: `PascalCase`
  - Functions/variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`

### JavaScript/React Code

Follow Airbnb JavaScript Style Guide:

```javascript
// Good
const KnowledgeNode = ({ nodeId, data, onSelect }) => {
  const [isSelected, setIsSelected] = useState(false);

  const handleClick = useCallback(() => {
    setIsSelected(true);
    onSelect(nodeId);
  }, [nodeId, onSelect]);

  return (
    <div className={isSelected ? 'node-selected' : 'node'}>
      {data.label}
    </div>
  );
};
```

**Guidelines:**
- Use functional components with hooks
- Use arrow functions for component definitions
- Destructure props
- Use `const` for variables that don't change
- Maximum line length: 100 characters
- Use meaningful component and variable names

### File Structure

```
# Python files
backend/
  service_name/
    __init__.py
    routes.py
    models.py
    services.py
    utils.py

# React files
components/
  FeatureName/
    index.js
    FeatureName.module.css
    FeatureName.test.js
```

## Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format
<type>(<scope>): <subject>

# Examples
feat(knowledge-graph): add node filtering capability
fix(auth): resolve JWT token expiration issue
docs(readme): update installation instructions
refactor(simulation): optimize layer 7 processing
test(api): add tests for compliance endpoints
chore(deps): update dependencies
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

**Guidelines:**
- Use present tense ("add feature" not "added feature")
- Use imperative mood ("move cursor to..." not "moves cursor to...")
- Keep subject line under 72 characters
- Reference issues and pull requests when relevant

## Pull Request Process

### Before Submitting

1. **Test your changes**
   ```bash
   # Run tests
   python -m pytest tests/

   # Run linting
   flake8 backend/ core/
   eslint components/ pages/
   ```

2. **Update documentation**
   - Update relevant README sections
   - Add/update docstrings
   - Update API documentation if applicable

3. **Update CHANGELOG.md**
   - Add your changes under "Unreleased" section

### Submitting the PR

1. **Push your changes**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request**
   - Use a clear, descriptive title
   - Fill out the PR template completely
   - Link related issues (e.g., "Closes #123")
   - Add screenshots for UI changes
   - Mark as draft if work in progress

3. **PR Description Template**
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   - [ ] Tests pass locally
   - [ ] Added new tests
   - [ ] Manual testing completed

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Comments added for complex code
   - [ ] Documentation updated
   - [ ] No new warnings generated

   ## Related Issues
   Closes #123
   ```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs automatically
2. **Code Review**: Maintainers review your code
3. **Revisions**: Address feedback and push updates
4. **Approval**: At least one maintainer approval required
5. **Merge**: Maintainers will merge your PR

## Testing Guidelines

### Writing Tests

```python
# Python test example
import pytest
from core.knowledge_graph import KnowledgeGraph

class TestKnowledgeGraph:
    @pytest.fixture
    def graph(self):
        return KnowledgeGraph()

    def test_add_node(self, graph):
        node_id = graph.add_node("test", {"label": "Test Node"})
        assert node_id is not None
        assert graph.get_node(node_id)["label"] == "Test Node"
```

```javascript
// JavaScript test example
import { render, screen } from '@testing-library/react';
import KnowledgeNode from '../components/KnowledgeNode';

describe('KnowledgeNode', () => {
  it('renders node label', () => {
    render(<KnowledgeNode data={{ label: 'Test' }} />);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });
});
```

### Test Coverage

- Aim for 80% code coverage
- Write tests for:
  - New features
  - Bug fixes
  - Edge cases
  - Critical business logic

### Running Tests

```bash
# Python tests
python -m pytest tests/ -v

# With coverage
python -m pytest --cov=core --cov=backend tests/

# JavaScript tests
npm test

# With coverage
npm test -- --coverage
```

## Documentation

### Code Documentation

- **Python**: Use docstrings (Google or NumPy style)
- **JavaScript**: Use JSDoc comments
- **Complex Logic**: Add inline comments explaining "why" not "what"

### Documentation Updates

When adding features, update:
- README.md (if it affects setup or usage)
- docs/API.md (for API changes)
- docs/ARCHITECTURE.md (for architectural changes)
- Inline code documentation

## Development Workflow

### Recommended Workflow

1. **Sync with upstream**
   ```bash
   git checkout main
   git pull upstream main
   ```

2. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature
   ```

3. **Make changes and commit**
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

4. **Push and create PR**
   ```bash
   git push origin feature/your-feature
   ```

5. **Respond to feedback**
   ```bash
   # Make changes based on review
   git add .
   git commit -m "fix(scope): address review feedback"
   git push origin feature/your-feature
   ```

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/updates

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/kherrera6219/DataLogicEngine/discussions)
- **Bug Reports**: Create an [Issue](https://github.com/kherrera6219/DataLogicEngine/issues)
- **Chat**: Join our community chat (if available)

## Recognition

Contributors will be recognized in:
- CHANGELOG.md
- Repository contributors list
- Annual contributor acknowledgments

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to DataLogicEngine!
