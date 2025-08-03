# Contributing

Thank you for your interest in contributing to the A2A Registry! This guide will help you get started with contributing to the project.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Make (for running development commands)

### Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/allenday/a2a-registry.git
   cd a2a-registry
   ```

2. **Initialize submodules:**
   ```bash
   git submodule update --init --recursive
   ```

3. **Set up development environment:**
   ```bash
   make setup
   ```

   This command will:
   - Create a virtual environment
   - Install development dependencies
   - Set up pre-commit hooks

4. **Verify the setup:**
   ```bash
   make dev-check
   ```

   This will run linting, type checking, and tests to ensure everything is working.

## Development Workflow

### Code Style and Standards

We use several tools to maintain code quality:

- **Black**: Code formatting
- **Ruff**: Linting and import sorting
- **MyPy**: Static type checking
- **Pytest**: Testing framework

### Running Quality Checks

```bash
# Format code
make format

# Run linting
make lint

# Run type checking
make typecheck

# Run tests
make test

# Run all checks
make dev-check
```

### Pre-commit Hooks

Pre-commit hooks are automatically installed during setup. They will:
- Format code with Black
- Check and fix imports with Ruff
- Run basic linting
- Check for common issues

To run pre-commit manually:
```bash
pre-commit run --all-files
```

## Project Structure

```
a2a-registry/
├── src/a2a_registry/           # Main source code
│   ├── __init__.py
│   ├── cli.py                  # Command line interface
│   ├── server.py               # FastAPI server implementation
│   ├── storage.py              # Data storage layer
│   └── proto/                  # Protocol buffer definitions
│       └── generated/          # Generated gRPC code
├── tests/                      # Test suite
├── docs/                       # Documentation source
├── proto/                      # Proto definitions
├── third_party/                # Third-party dependencies
├── Makefile                    # Development commands
├── pyproject.toml              # Project configuration
└── mkdocs.yml                  # Documentation configuration
```

## Making Changes

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clean, well-documented code
- Follow existing code patterns and conventions
- Add or update tests for your changes
- Update documentation if needed

### 3. Test Your Changes

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run full development checks
make dev-check
```

### 4. Update Documentation

If your changes affect the API or user-facing functionality:

```bash
# Serve documentation locally to preview changes
make docs-serve

# Build documentation
make docs-build
```

### 5. Commit Your Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

We follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions/changes
- `refactor:` for code refactoring
- `chore:` for maintenance tasks

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with:
- Clear description of changes
- Reference to any related issues
- Screenshots if UI changes are involved

## Testing Guidelines

### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names
- Test both success and error cases
- Use pytest fixtures for common setup

Example test structure:
```python
import pytest
from a2a_registry.server import create_app

@pytest.fixture
def app():
    return create_app()

@pytest.fixture  
def client(app):
    return TestClient(app)

def test_register_agent_success(client):
    # Test successful agent registration
    pass

def test_register_agent_invalid_data(client):
    # Test error handling for invalid data
    pass
```

### Test Coverage

We aim for high test coverage. Run coverage reports with:
```bash
make test-cov
```

### Integration Tests

For features that involve multiple components, write integration tests that:
- Test the full request/response cycle
- Verify proper error handling
- Check data persistence

## Protocol Buffer Changes

If you need to modify the gRPC interface:

1. **Edit the proto files:**
   - `proto/registry.proto` for registry-specific messages
   - Update third-party protos if needed

2. **Regenerate code:**
   ```bash
   make proto
   ```

3. **Update implementation:**
   - Modify server code to match new proto definitions
   - Update client examples
   - Add tests for new functionality

4. **Update documentation:**
   - Update API documentation
   - Add examples for new methods

## Documentation

### Writing Documentation

- Use clear, concise language
- Include code examples
- Add diagrams where helpful
- Keep examples up-to-date

### Documentation Structure

- `docs/index.md` - Main landing page
- `docs/getting-started/` - Installation and setup guides
- `docs/api/` - API reference and examples
- `docs/developer/` - Development guides
- `docs/examples/` - Usage examples

### Building Documentation

```bash
# Install documentation dependencies
make docs-install

# Serve locally (auto-reloads on changes)
make docs-serve

# Build static site
make docs-build

# Deploy to GitHub Pages
make docs-deploy
```

## Release Process

Releases are handled by maintainers. The process includes:

1. Update version in `pyproject.toml`
2. Update changelog
3. Create release tag
4. Build and publish to PyPI
5. Deploy documentation
6. Create GitHub release

## Getting Help

- **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/allenday/a2a-registry/issues)
- **Discussions**: Ask questions on [GitHub Discussions](https://github.com/allenday/a2a-registry/discussions)
- **Code Review**: All changes go through pull request review

## Code of Conduct

Please be respectful and constructive in all interactions. We aim to create a welcoming environment for all contributors.

## Recognition

Contributors are recognized in:
- Release notes
- Contributors section of documentation
- Git commit history

Thank you for contributing to the A2A Registry! 🚀