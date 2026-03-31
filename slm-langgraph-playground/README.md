# slm-langgraph-playground

A minimal local-first Python playground for running Small Language Models (SLMs) with Ollama, orchestrating them with LangGraph, and tracing executions with Langfuse.

This project is intentionally small. It is designed to show how to:

- run local models on a laptop or workstation
- switch between multiple Ollama-installed SLMs
- keep the orchestration flow readable with LangGraph
- add optional observability with Langfuse

## Why local SLMs

Local models are useful when you want:

- fast experimentation without cloud dependencies
- lower cost for repeated testing
- more control over data locality
- side-by-side model comparison on the same machine

## Architecture

```text
               +----------------------+
Prompt ------> | LangGraph Input Node | ------------------+
               +----------------------+                   |
                                                          v
                                              +----------------------+
                                              | LangGraph Model Node |
                                              |  Ollama REST client  |
                                              +----------------------+
                                                          |
                                                          v
                                              +----------------------+
                                              | Evaluator Node       |
                                              | metrics + timestamp  |
                                              +----------------------+
                                                          |
                                                          v
                                            structured JSON result

Langfuse spans:
- graph_execution
- model_call
- evaluation
```

## Project Layout

```text
slm-langgraph-playground/
|-- README.md
|-- pyproject.toml
|-- requirements.txt
|-- .env.example
|-- Makefile
|-- scripts/
|-- app/
`-- tests/
```

## Quick Start

1. Create a Python virtual environment.

```bash
python -m venv .venv
```

2. Activate the virtual environment.

On macOS or Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

3. Install Ollama.

```bash
bash scripts/install_ollama.sh
```

4. Install Python dependencies.

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

You can also use:

```bash
make setup
```

`make setup` creates `.venv` if it does not exist and installs dependencies into that virtual environment.

On Windows PowerShell, use:

```powershell
.\scripts\setup.ps1
```

5. Start Ollama locally.

```bash
bash scripts/run_ollama.sh
```

On Windows PowerShell:

```powershell
.\scripts\run_ollama.ps1
```

6. Copy environment defaults.

```bash
cp .env.example .env
```

7. Pull the example models.

```bash
bash scripts/pull_models.sh
```

On Windows PowerShell:

```powershell
.\scripts\pull_models.ps1
```

8. Run the CLI example.

```bash
make run-cli
```

On Windows PowerShell:

```powershell
.\scripts\run_cli.ps1
```

## Python Environment Setup

This repository includes both:

- `pyproject.toml` for package metadata
- `requirements.txt` for quick local dependency installation

Recommended local setup:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
cp .env.example .env
```

On Windows PowerShell, replace the activation command with:

```powershell
.venv\Scripts\Activate.ps1
```

If you prefer `make`, you do not need to activate the environment first. `make setup` installs into `.venv`, and the local run scripts prefer that interpreter automatically.

On native Windows PowerShell, `make` is usually not installed. Use the PowerShell scripts in `scripts/` instead.

## Ollama Setup

This project only supports local Ollama calls.

- allowed hosts: `localhost`, `127.0.0.1`
- default endpoint: `http://127.0.0.1:11434/api/chat`
- streaming is disabled to keep the example simple

To verify Ollama:

```bash
ollama --version
curl http://127.0.0.1:11434/api/tags
```

Windows install reference:

```powershell
.\scripts\install_ollama.ps1
```

## Pull Models

Models are read from `AVAILABLE_MODELS` in `.env`.

Example:

```env
PRIMARY_MODEL=phi4-mini
AVAILABLE_MODELS=phi4-mini,qwen3:4b,llama3.2:3b
```

Pull them with:

```bash
bash scripts/pull_models.sh
```

On Windows PowerShell:

```powershell
.\scripts\pull_models.ps1
```

## Run the CLI

```bash
python -m app.cli --prompt "Explain what an API gateway is" --model phi4-mini
```

On Windows PowerShell:

```powershell
.\scripts\run_cli.ps1 -Prompt "Explain what an API gateway is" -Model "phi4-mini"
```

Example output:

```json
{
  "input": "Explain what an API gateway is",
  "model": "phi4-mini",
  "response": "An API gateway is a front door that routes, secures, and manages API requests.",
  "timestamp": "2026-03-31T10:45:12.184512+00:00",
  "metrics": {
    "word_count": 14,
    "char_count": 82,
    "latency_ms": 241.903
  }
}
```

## Run the API

Start the local API server:

```bash
bash scripts/run_api.sh
```

On Windows PowerShell:

```powershell
.\scripts\run_api.ps1
```

Send a request:

```bash
curl -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"Summarize retrieval-augmented generation\",\"model\":\"qwen3:4b\"}"
```

The FastAPI server is intended for local use only and should be bound to `127.0.0.1`.

## Langfuse

Langfuse is optional.

If these variables are set, traces are sent automatically:

```env
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
```

If the keys are empty, the app runs normally with tracing disabled.

## Switch Models

You can switch models in three ways:

1. CLI argument:

```bash
python -m app.cli --prompt "Compare HTTP and gRPC" --model llama3.2:3b
```

2. Environment variable:

```bash
MODEL=qwen3:4b python -m app.cli --prompt "What is LangGraph?"
```

3. API body:

```json
{
  "prompt": "Explain embeddings",
  "model": "phi4-mini"
}
```

## Extend the Pipeline

The graph lives in `app/graph.py` and currently has three nodes:

- `input_node`
- `model_node`
- `evaluator_node`

Easy extensions:

- add a safety or policy node before model execution
- add a second evaluator for rubric-style scoring
- add a comparison runner that executes the same prompt across several models

## Make Targets

```bash
make setup
make pull-models
make run-ollama
make run-cli
make run-api
make test
```

## PowerShell Commands

```powershell
.\scripts\setup.ps1
.\scripts\run_ollama.ps1
.\scripts\pull_models.ps1
.\scripts\run_cli.ps1 -Prompt "Explain what an API gateway is" -Model "phi4-mini"
.\scripts\run_api.ps1
```

## Tests

Run the test suite:

```bash
make test
```

The tests use a fake Ollama client, so they do not require Ollama to be running.
