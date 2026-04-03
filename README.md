# slm-langgraph-playground

A minimal local-first playground for running Small Language Models (SLMs) with Ollama, orchestrating them with LangGraph, and tracing executions with Langfuse.

This repo is intentionally small. It is meant to show how to:

- run local models on a laptop or workstation
- switch between multiple Ollama-installed SLMs
- keep the orchestration flow readable with LangGraph
- add optional observability with Langfuse

## Requirements

- Python 3.11+
- Ollama installed locally
- one or more models available in Ollama
- optional Langfuse API keys if you want tracing

This project only supports local Ollama calls.

- allowed hosts: `localhost`, `127.0.0.1`
- default Ollama endpoint: `http://127.0.0.1:11434/api/chat`
- `/run` returns a completed response
- `/stream` is available for incremental chat UI updates

## Quick Start

Before testing the agent, make sure Ollama is installed, running locally, and has at least one model already pulled. The CLI and API both depend on a live local Ollama instance.

All commands below now assume you are already in the repository root.

### macOS or Linux

If Ollama is not installed yet:

```bash
bash scripts/install_ollama.sh
```

Set up the project:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
cp .env.example .env
bash scripts/run_ollama.sh
bash scripts/pull_models.sh
python -m app.cli --prompt "Explain what an API gateway is" --model phi4-mini
```

If you prefer `make`:

```bash
make setup
cp .env.example .env
make run-ollama
make pull-models
make run-cli
```

### Windows PowerShell

If Ollama is not installed yet:

```powershell
.\scripts\install_ollama.ps1
```

Set up the project:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
Copy-Item .env.example .env
.\scripts\run_ollama.ps1
.\scripts\pull_models.ps1
.\scripts\run_cli.ps1 -Prompt "Explain what an API gateway is" -Model "phi4-mini"
```

Or use the included setup script:

```powershell
.\scripts\setup.ps1
Copy-Item .env.example .env
.\scripts\run_ollama.ps1
.\scripts\pull_models.ps1
.\scripts\run_cli.ps1 -Prompt "Explain what an API gateway is" -Model "phi4-mini"
```

## Configuration

Copy `.env.example` to `.env` and update the values you care about.

Core settings:

```env
OLLAMA_HOST=127.0.0.1
OLLAMA_PORT=11434
PRIMARY_MODEL=phi4-mini
AVAILABLE_MODELS=phi4-mini,qwen3:4b,llama3.2:3b
MODEL=
LOG_LEVEL=INFO
REQUEST_TIMEOUT_S=120
```

Notes:

- `PRIMARY_MODEL` is the default model for the app
- `AVAILABLE_MODELS` is the allowed model list
- `MODEL` is an optional runtime override
- `REQUEST_TIMEOUT_S` controls how long the app waits for Ollama before failing the request
- models listed in `AVAILABLE_MODELS` should also be pulled into Ollama

To verify Ollama is running:

```bash
ollama --version
curl http://127.0.0.1:11434/api/tags
```

Before running `app.cli` or the API server for real testing, confirm that Ollama is already active and responding on `127.0.0.1:11434`.

### Langfuse

Langfuse is optional. If these variables are set, traces are sent automatically:

```env
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PROJECT_NAME=
```

Notes:

- if the keys are empty, the app runs normally with tracing disabled
- `LANGFUSE_PROJECT_NAME` is app-level trace metadata, not the native Langfuse project selector
- the actual Langfuse project is determined by the API keys you provide
- for self-hosted instances, set `LANGFUSE_HOST` to your Langfuse base URL

If you want to use Langfuse Cloud with a personal account:

- create a free Langfuse Cloud account: https://langfuse.com/pricing
- follow the official tracing setup guide: https://langfuse.com/docs/observability/get-started
- create a project and generate API credentials in the Langfuse project settings
- copy the keys into `.env` before testing this agent

Langfuse self-hosting reference:

- https://langfuse.com/self-hosting/configuration

## Run the Project

Prerequisite: Ollama must already be running locally before you test the agent. If it is not running, model calls will fail.

### CLI

```bash
python -m app.cli --prompt "Explain what an API gateway is" --model phi4-mini
```

Windows PowerShell:

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

### API

Start the local API server:

```bash
bash scripts/run_api.sh
```

Windows PowerShell:

```powershell
.\scripts\run_api.ps1
```

Open the built-in chat UI:

```text
http://127.0.0.1:8000/chat
```

Send a request:

```bash
curl -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"Summarize retrieval-augmented generation\",\"model\":\"qwen3:4b\"}"
```

The FastAPI server is intended for local use only and binds to `127.0.0.1`.

If Ollama exceeds `REQUEST_TIMEOUT_S`, `/run` now returns `504 Gateway Timeout` with a clearer model-specific message.

### Web Chat

The built-in chat UI is served by the same FastAPI app and requires no extra frontend tooling.

To run it:

1. make sure Ollama is already running locally on `127.0.0.1:11434`
2. start the FastAPI server with `bash scripts/run_api.sh` or `.\scripts\run_api.ps1`
3. open `http://127.0.0.1:8000/chat` in your browser

- route: `http://127.0.0.1:8000/chat`
- model selector populated from `AVAILABLE_MODELS`
- multi-turn context by sending the full `messages` history on each request
- streaming UI updates from `/stream`, so slow models no longer look frozen while generating
- browser-managed transcript, so the backend stays stateless

You can also send a full conversation over the API:

```bash
curl -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -d "{
    \"model\":\"phi4-mini\",
    \"messages\":[
      {\"role\":\"user\",\"content\":\"Hi\"},
      {\"role\":\"assistant\",\"content\":\"Hello, how can I help?\"},
      {\"role\":\"user\",\"content\":\"Summarize retrieval-augmented generation\"}
    ]
  }"
```

Rules:

- use either `prompt` or `messages`
- `messages` accepts `user` and `assistant` roles
- the app still prepends its own internal system prompt before calling Ollama
- `/run` returns a complete JSON response, while `/stream` emits newline-delimited JSON events for incremental UI updates

### Switch Models

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

## How It Works

### Architecture

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

### Node Responsibilities

The LangGraph pipeline currently contains three nodes:

- `input_node`: takes the normalized conversation and converts it into the message list sent to the model
- `model_node`: calls Ollama with the selected model, captures the generated response, and emits the `model_call` trace
- `evaluator_node`: computes simple output metrics such as latency, word count, char count, and timestamp, then emits the `evaluation` trace

### Prompt Location and Variations

Prompt templates currently live in `app/prompts.py`.

Today the flow is:

1. the request is normalized into a conversation of `user` and `assistant` turns
2. the latest user turn is stored as `state["input"]` for evaluation metadata
3. `input_node` calls `build_messages(messages=state["conversation"])`
4. `build_messages()` prepends the internal system prompt and returns the final list sent to Ollama

The current prompt setup is intentionally simple:

- `SYSTEM_PROMPT` defines the default assistant behavior
- `build_messages(...)` returns one system message plus the normalized conversation history

If you want to change prompt behavior:

- edit `SYSTEM_PROMPT` to change the default instruction applied to every request
- edit `build_messages()` to add extra context, few-shot examples, guardrails, or formatting instructions
- keep prompt-building logic in `app/prompts.py` and use `input_node` as the place where you decide which prompt variant to build

If you want to add multiple prompt styles, a simple pattern is:

- add new builder functions such as `build_summary_messages()`, `build_rag_messages()`, or `build_classifier_messages()`
- route to the right builder inside `input_node`
- optionally expose the choice through a new CLI argument, API field, or graph state value

### Project Layout

```text
repository-root/
|-- README.md
|-- pyproject.toml
|-- requirements.txt
|-- .env.example
|-- Makefile
|-- scripts/
|-- app/
`-- tests/
```

### Extend the Pipeline

The graph lives in `app/graph.py` and currently has three nodes:

- `input_node` for prompt preparation
- `model_node` for Ollama inference
- `evaluator_node` for response scoring and metadata

Easy extensions:

- add a safety or policy node before model execution
- add a second evaluator for rubric-style scoring
- add a comparison runner that executes the same prompt across several models

## Development

### Useful Commands

These commands assume you are in the repository root.

Make targets:

```bash
make setup
make pull-models
make run-ollama
make run-cli
make run-api
make test
```

PowerShell commands:

```powershell
.\scripts\setup.ps1
.\scripts\run_ollama.ps1
.\scripts\pull_models.ps1
.\scripts\run_cli.ps1 -Prompt "Explain what an API gateway is" -Model "phi4-mini"
.\scripts\run_api.ps1
```

### Tests

Run the test suite:

```bash
make test
```

The tests use a fake Ollama client, so Ollama does not need to be running.
