.PHONY: help install install-dev clean lint format type-check test test-cov build proto submodules setup
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

type-check: ## Run type checking with mypy
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

dev-check: lint type-check test ## Run all development checks

ci: install-dev lint type-check test ## Run CI pipeline locally