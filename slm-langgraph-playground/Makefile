.PHONY: setup pull-models run-ollama run-cli run-api test

VENV_DIR := .venv

ifeq ($(OS),Windows_NT)
VENV_PYTHON := $(VENV_DIR)/Scripts/python.exe
else
VENV_PYTHON := $(VENV_DIR)/bin/python
endif

setup:
	python -m venv $(VENV_DIR)
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements.txt
	$(VENV_PYTHON) -m pip install -e .

pull-models:
	bash scripts/pull_models.sh

run-ollama:
	bash scripts/run_ollama.sh

run-cli:
	bash scripts/run_cli.sh

run-api:
	bash scripts/run_api.sh

test:
	$(VENV_PYTHON) -m pytest
