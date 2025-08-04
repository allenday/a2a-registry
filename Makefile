.PHONY: help install install-dev clean lint format typecheck test test-cov build proto submodules setup env-setup env-load deploy-build deploy-push deploy-local deploy-gcp terraform-init terraform-plan terraform-apply terraform-destroy terraform-plan-gh terraform-apply-gh terraform-destroy-gh terraform-status
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

lint: install-dev ## Run linting with ruff
	$(PYTHON_VENV) -m ruff check $(SRC_DIR)

typecheck: install-dev ## Run type checking with mypy
	$(PYTHON_VENV) -m mypy $(SRC_DIR)

test: install-dev ## Run tests
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
		--mypy_out=$(GENERATED_DIR) \
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

release: build ## Build and prepare for release (dry run)
	@echo "Release build complete!"
	@echo "Distribution packages created in dist/"
	@echo "To publish to TestPyPI: make publish-test"
	@echo "To publish to PyPI: make publish"
	@echo "To create a GitHub release, use the manual workflow in GitHub Actions"

release-prepare: ## Prepare a new release (updates version and builds)
	@echo "Usage: python scripts/release.py <version>"
	@echo "Example: python scripts/release.py 0.1.1"

env-setup: ## Set up environment variables from example
	@echo "Setting up environment variables..."
	@if [ -f "env.example" ]; then \
		if [ -f ".env" ]; then \
			echo "⚠️  .env file already exists. Backing up to .env.backup"; \
			cp .env .env.backup; \
		fi; \
		cp env.example .env; \
		echo "✅ Created .env from env.example"; \
		echo "📝 Please edit .env file with your specific values"; \
	else \
		echo "❌ env.example not found"; \
		exit 1; \
	fi

env-load: ## Load environment variables into current shell
	@echo "Loading environment variables..."
	@if [ -f ".env" ]; then \
		export $$(cat .env | grep -v '^#' | xargs); \
		echo "✅ Environment variables loaded"; \
		echo "Current GCP_PROJECT_ID: $$GCP_PROJECT_ID"; \
		echo "Current GCP_REGION: $$GCP_REGION"; \
	else \
		echo "❌ .env file not found. Run 'make env-setup' first"; \
		exit 1; \
	fi

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

# Deployment commands
deploy-build: ## Build Docker image for deployment
	@echo "Building Docker image..."
	docker build -f deploy/Dockerfile -t gcr.io/$(shell grep GCP_PROJECT_ID .env | cut -d'=' -f2)/a2a-registry:latest .

deploy-push: deploy-build ## Build and push Docker image to GCR
	@echo "Pushing Docker image to GCR..."
	docker push gcr.io/$(shell grep GCP_PROJECT_ID .env | cut -d'=' -f2)/a2a-registry:latest

deploy-local: ## Deploy to local Kubernetes (requires minikube or kind)
	@echo "Deploying to local Kubernetes..."
	kubectl apply -f deploy/k8s/

deploy-gcp: deploy-push ## Deploy to GCP (build, push, and deploy)
	@echo "Deploying to GCP..."
	@echo "Make sure you have gcloud configured and authenticated"
	gcloud container clusters get-credentials $(shell grep GCP_CLUSTER_NAME .env | cut -d'=' -f2) --region $(shell grep GCP_REGION .env | cut -d'=' -f2) --project $(shell grep GCP_PROJECT_ID .env | cut -d'=' -f2)
	kubectl set image deployment/a2a-registry a2a-registry=gcr.io/$(shell grep GCP_PROJECT_ID .env | cut -d'=' -f2)/a2a-registry:latest
	kubectl rollout status deployment/a2a-registry

terraform-init: ## Initialize Terraform
	@echo "Initializing Terraform..."
	cd deploy/terraform && terraform init

terraform-plan: terraform-init ## Plan Terraform changes
	@echo "Planning Terraform changes..."
	cd deploy/terraform && terraform plan

terraform-apply: terraform-init ## Apply Terraform changes
	@echo "Applying Terraform changes..."
	cd deploy/terraform && terraform apply -auto-approve

terraform-destroy: ## Destroy Terraform resources
	@echo "⚠️  DESTROYING INFRASTRUCTURE!"
	@echo "⚠️  This will delete all GCP resources!"
	cd deploy/terraform && terraform destroy -auto-approve

# GitHub Actions Terraform triggers
terraform-plan-gh: ## Plan Terraform changes via GitHub Actions
	@echo "Triggering Terraform plan via GitHub Actions..."
	@echo "Visit: https://github.com/allenday/a2a-registry/actions/workflows/terraform.yml"
	@echo "Or run manually: gh workflow run terraform.yml --field action=plan"

terraform-apply-gh: ## Apply Terraform changes via GitHub Actions
	@echo "Triggering Terraform apply via GitHub Actions..."
	@echo "⚠️  This will apply infrastructure changes!"
	@echo "Run manually: gh workflow run terraform.yml --field action=apply --field auto_approve=true"

terraform-destroy-gh: ## Destroy Terraform resources via GitHub Actions
	@echo "⚠️  DESTROYING INFRASTRUCTURE!"
	@echo "⚠️  This will delete all GCP resources!"
	@echo "Run manually: gh workflow run terraform.yml --field action=destroy --field auto_approve=true"

terraform-status: ## Check Terraform workflow status
	@echo "Checking Terraform workflow status..."
	gh run list --workflow=terraform.yml --limit=5