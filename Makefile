.PHONY: help install install-dev clean lint format typecheck test test-cov build proto submodules setup
.DEFAULT_GOAL := help

# Python and virtual environment
PYTHON := python3
VENV := .venv
PYTHON_VENV := $(VENV)/bin/python
PIP_VENV := $(VENV)/bin/pip

# Directories
SRC_DIR := src
PROTO_DIR := $(SRC_DIR)/a2a_registry/proto
GENERATED_DIR := $(PROTO_DIR)/generated
THIRD_PARTY := third_party

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: submodules install-dev ## Complete project setup

submodules: ## Initialize and update git submodules
	git submodule update --init --recursive

$(VENV): ## Create virtual environment
	$(PYTHON) -m venv $(VENV)
	$(PIP_VENV) install --upgrade pip setuptools wheel

install: $(VENV) ## Install package in development mode
	$(PIP_VENV) install -e .

install-dev: $(VENV) ## Install package with development dependencies
	$(PIP_VENV) install -e ".[dev]"

clean: ## Clean build artifacts and cache files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

format: ## Format code with black
	$(PYTHON_VENV) -m black $(SRC_DIR)
	$(PYTHON_VENV) -m ruff check --fix $(SRC_DIR)

lint: ## Run linting with ruff
	$(PYTHON_VENV) -m ruff check $(SRC_DIR)

typecheck: ## Run type checking with mypy
	$(PYTHON_VENV) -m mypy $(SRC_DIR)

test: ## Run tests
	$(PYTHON_VENV) -m pytest

test-cov: ## Run tests with coverage
	$(PYTHON_VENV) -m pytest --cov=$(SRC_DIR) --cov-report=html --cov-report=term

proto: ## Generate protobuf files
	@echo "Generating protobuf files..."
	mkdir -p $(GENERATED_DIR)
	$(PYTHON_VENV) -m grpc_tools.protoc \
		--proto_path=proto \
		--proto_path=$(THIRD_PARTY)/a2a/specification/grpc \
		--proto_path=$(THIRD_PARTY)/api-common-protos \
		--python_out=$(GENERATED_DIR) \
		--grpc_python_out=$(GENERATED_DIR) \
		proto/*.proto \
		$(THIRD_PARTY)/a2a/specification/grpc/*.proto
	@echo "Protobuf generation complete"

build: clean install-dev ## Build distribution packages
	$(PYTHON_VENV) -m build
	$(PYTHON_VENV) -m twine check dist/*

publish-test: build ## Publish to TestPyPI
	$(PYTHON_VENV) -m twine upload --repository testpypi dist/*

publish: build ## Publish to PyPI
	$(PYTHON_VENV) -m twine upload dist/*

dev-check: lint typecheck test ## Run all development checks

ci: install-dev lint typecheck test ## Run CI pipeline locally

# Documentation commands
docs-install: $(VENV) ## Install documentation dependencies
	$(PIP_VENV) install -e ".[docs]"

docs-serve: docs-install ## Serve documentation locally
	$(PYTHON_VENV) -m mkdocs serve

docs-build: docs-install ## Build documentation
	$(PYTHON_VENV) -m mkdocs build

docs-deploy: docs-build ## Build documentation (deployment handled by GitHub Actions)
	@echo "Documentation built successfully. Deployment is handled automatically by GitHub Actions when pushing to master."

# Development scripts
dev-server: install-dev ## Start development server with auto-reload
	$(PYTHON_VENV) -c "from a2a_registry.server import create_app; import uvicorn; uvicorn.run(create_app(), host='127.0.0.1', port=8000, reload=True, factory=True)"

dev-setup-complete: setup ## Complete development setup including pre-commit hooks
	$(PYTHON_VENV) -m pre-commit install
	@echo "Development environment setup complete!"
	@echo "Try: make dev-server"

check-all: lint typecheck test docs-build ## Run all checks (linting, typing, tests, docs)

pre-commit: ## Run pre-commit hooks on all files
	$(PYTHON_VENV) -m pre-commit run --all-files

update-deps: ## Update all dependencies to latest versions
	$(PIP_VENV) install --upgrade pip setuptools wheel
	$(PIP_VENV) install --upgrade -e ".[dev,docs]"

reset-env: clean ## Reset development environment
	rm -rf $(VENV)
	make setup