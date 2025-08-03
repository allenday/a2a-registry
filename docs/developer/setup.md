# Development Setup

This guide walks you through setting up a development environment for the A2A Registry.

## Prerequisites

### Required Software

- **Python 3.9+**: The minimum supported version
- **Git**: For version control and submodule management
- **Make**: For running development commands (included on Linux/macOS, install via chocolatey on Windows)

### Optional Tools

- **Docker**: For containerized development
- **gRPC tools**: For Protocol Buffer compilation
- **IDE/Editor**: VS Code, PyCharm, or your preferred editor

## Quick Setup

The fastest way to get started:

```bash
# Clone and setup everything
git clone https://github.com/allenday/a2a-registry.git
cd a2a-registry
make setup
```

This single command will:
1. Initialize git submodules
2. Create a Python virtual environment
3. Install all dependencies (including development tools)
4. Set up pre-commit hooks

## Manual Setup

If you prefer to set things up step by step:

### 1. Clone the Repository

```bash
git clone https://github.com/allenday/a2a-registry.git
cd a2a-registry
```

### 2. Initialize Submodules

The project includes the A2A specification as a submodule:

```bash
git submodule update --init --recursive
```

### 3. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 4. Install Dependencies

```bash
# Install package in development mode with all dependencies
pip install -e ".[dev,docs]"
```

### 5. Set Up Pre-commit Hooks

```bash
pre-commit install
```

### 6. Generate Protocol Buffers

```bash
make proto
```

## Verify Installation

Run the development checks to ensure everything is working:

```bash
make dev-check
```

This will run:
- Code linting (ruff)
- Type checking (mypy)
- All tests (pytest)

## Development Commands

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Type checking
make typecheck
```

### Testing

```bash
# Run all tests
make test

# Run tests with coverage report
make test-cov

# Run specific test file
pytest tests/test_server.py -v
```

### Documentation

```bash
# Install documentation dependencies
make docs-install

# Serve documentation locally
make docs-serve

# Build documentation
make docs-build
```

### Protocol Buffers

```bash
# Regenerate protobuf files
make proto
```

### Server Development

```bash
# Start development server
a2a-registry serve --reload

# Start with custom configuration
a2a-registry serve --host 0.0.0.0 --port 8080 --debug
```

## IDE Configuration

### VS Code

Recommended extensions:
- Python
- Pylance
- autoDocstring
- GitLens
- Protocol Buffers

Example `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".pytest_cache": true,
    ".mypy_cache": true,
    ".ruff_cache": true
  }
}
```

### PyCharm

Configure PyCharm to:
- Use the project's virtual environment (`.venv`)
- Set Black as the code formatter
- Enable Ruff as the linter
- Configure pytest as the test runner

## Environment Variables

For development, you can set these environment variables:

```bash
# Server configuration
export A2A_REGISTRY_HOST=0.0.0.0
export A2A_REGISTRY_PORT=8000
export A2A_REGISTRY_DEBUG=true
export A2A_REGISTRY_LOG_LEVEL=DEBUG

# Development tools
export PYTHONPATH=src:$PYTHONPATH
```

Create a `.env` file for local development:
```env
A2A_REGISTRY_DEBUG=true
A2A_REGISTRY_LOG_LEVEL=DEBUG
```

## Docker Development

For containerized development:

### Build Development Image

```bash
docker build -t a2a-registry-dev .
```

### Run Development Container

```bash
docker run -it --rm \
  -p 8000:8000 \
  -v $(pwd):/app \
  a2a-registry-dev \
  a2a-registry serve --host 0.0.0.0
```

### Docker Compose

Create `docker-compose.dev.yml`:
```yaml
version: '3.8'
services:
  registry:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - A2A_REGISTRY_DEBUG=true
    command: a2a-registry serve --host 0.0.0.0 --reload
```

Run with:
```bash
docker-compose -f docker-compose.dev.yml up
```

## Troubleshooting

### Common Issues

**Virtual environment not activated:**
```bash
# Make sure you're in the virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

**Missing dependencies:**
```bash
# Reinstall all dependencies
pip install -e ".[dev,docs]"
```

**Protocol buffer compilation errors:**
```bash
# Clean and regenerate
rm -rf src/a2a_registry/proto/generated/*
make proto
```

**Pre-commit hook failures:**
```bash
# Run pre-commit on all files
pre-commit run --all-files

# Skip hooks temporarily (not recommended)
git commit --no-verify
```

**Import errors:**
```bash
# Add source directory to Python path
export PYTHONPATH=src:$PYTHONPATH

# Or install in development mode
pip install -e .
```

### Performance Issues

**Slow tests:**
```bash
# Run tests in parallel
pytest -n auto

# Run only modified tests
pytest --lf
```

**Slow linting:**
```bash
# Run only on changed files
ruff check $(git diff --name-only HEAD~1 | grep '\.py$')
```

## Advanced Setup

### Custom Python Version

Using pyenv to manage Python versions:
```bash
# Install Python 3.11
pyenv install 3.11.0
pyenv local 3.11.0

# Create virtual environment
python -m venv .venv
```

### Development with Multiple Registries

For testing distributed scenarios:
```bash
# Start multiple registry instances
a2a-registry serve --port 8000 &
a2a-registry serve --port 8001 &
a2a-registry serve --port 8002 &
```

### Profiling and Debugging

```bash
# Install profiling tools
pip install py-spy memory-profiler

# Profile the server
py-spy record -o profile.svg -- a2a-registry serve

# Memory profiling
mprof run a2a-registry serve
mprof plot
```

## Next Steps

After setting up your development environment:

1. Read the [Contributing Guide](contributing.md)
2. Explore the [API Documentation](../api/overview.md)
3. Try the [Examples](../examples/basic-usage.md)
4. Run the [Testing Guide](testing.md)