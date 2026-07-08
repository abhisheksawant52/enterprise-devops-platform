.DEFAULT_GOAL := help
SHELL := /bin/bash

VENV        := .venv
PYTHON      := $(VENV)/bin/python
PIP         := $(VENV)/bin/pip
IMAGE       := ghcr.io/abhisheksawant52/edp-control-plane
TAG         ?= dev
APP_MODULE  := app.main:app

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: ## Create venv and install runtime + dev dependencies
	python -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r src/requirements.txt -r src/requirements-dev.txt

.PHONY: fmt
fmt: ## Auto-format the codebase
	$(VENV)/bin/black src tests
	$(VENV)/bin/ruff check --fix src tests

.PHONY: lint
lint: ## Lint (ruff) and check formatting (black)
	$(VENV)/bin/ruff check src tests
	$(VENV)/bin/black --check src tests

.PHONY: typecheck
typecheck: ## Static type checking with mypy
	$(VENV)/bin/mypy src

.PHONY: test
test: ## Run the test suite with coverage
	$(VENV)/bin/pytest

.PHONY: run
run: ## Run the control plane locally
	cd src && ../$(VENV)/bin/uvicorn $(APP_MODULE) --reload --host 0.0.0.0 --port 8000

.PHONY: build
build: ## Build the container image
	docker build -t $(IMAGE):$(TAG) -f src/Dockerfile src

.PHONY: tf-fmt
tf-fmt: ## Format all Terraform files
	terraform fmt -recursive terraform

.PHONY: tf-validate
tf-validate: ## Validate the dev environment
	cd terraform/environments/dev && terraform init -backend=false && terraform validate

.PHONY: helm-lint
helm-lint: ## Lint the Helm chart
	helm lint helm/chart

.PHONY: clean
clean: ## Remove caches and build artifacts
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
