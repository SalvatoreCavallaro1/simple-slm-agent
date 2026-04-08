from __future__ import annotations

from fastapi.testclient import TestClient

from app import api as api_module
from app.ollama_client import OllamaTimeoutError


client = TestClient(api_module.app)


def test_chat_page_is_served() -> None:
    response = client.get("/chat")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "SLM Chat" in response.text


def test_chat_config_returns_available_models() -> None:
    response = client.get("/chat/config")

    assert response.status_code == 200
    payload = response.json()
    assert payload["primary_model"] == api_module.settings.primary_model
    assert payload["available_models"] == list(api_module.settings.available_models)
    assert payload["request_timeout_s"] == api_module.settings.request_timeout_s


def test_run_endpoint_accepts_message_history(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_prompt(
        prompt: str | None = None,
        *,
        model: str | None = None,
        messages: list[dict[str, str]] | None = None,
        settings=None,
        ollama_client=None,
    ) -> dict[str, object]:
        captured["prompt"] = prompt
        captured["model"] = model
        captured["messages"] = messages
        return {
            "input": "What is LangGraph?",
            "model": model or "phi4-mini",
            "response": "A graph-based orchestration library for LLM workflows.",
            "timestamp": "2026-04-03T15:00:00+00:00",
            "metrics": {
                "word_count": 8,
                "char_count": 54,
                "latency_ms": 12.5,
            },
        }

    monkeypatch.setattr(api_module, "run_prompt", fake_run_prompt)

    response = client.post(
        "/run",
        json={
            "model": "qwen3:4b",
            "messages": [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello"},
                {"role": "user", "content": "What is LangGraph?"},
            ],
        },
    )

    assert response.status_code == 200
    assert captured["prompt"] is None
    assert captured["model"] == "qwen3:4b"
    assert captured["messages"] == [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello"},
        {"role": "user", "content": "What is LangGraph?"},
    ]


def test_run_endpoint_rejects_prompt_and_messages_together() -> None:
    response = client.post(
        "/run",
        json={
            "prompt": "Hello",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Provide either 'prompt' or 'messages', not both."


def test_run_endpoint_maps_ollama_timeout_to_504(monkeypatch) -> None:
    def fake_run_prompt(
        prompt: str | None = None,
        *,
        model: str | None = None,
        messages: list[dict[str, str]] | None = None,
        settings=None,
        ollama_client=None,
    ) -> dict[str, object]:
        raise OllamaTimeoutError("Ollama timed out after 120 seconds for model 'qwen3.5:0.8b'.")

    monkeypatch.setattr(api_module, "run_prompt", fake_run_prompt)

    response = client.post(
        "/run",
        json={"prompt": "Hello", "model": "qwen3.5:0.8b"},
    )

    assert response.status_code == 504
    assert response.json()["detail"] == "Ollama timed out after 120 seconds for model 'qwen3.5:0.8b'."


def test_stream_endpoint_returns_ndjson_events(monkeypatch) -> None:
    def fake_stream_chat_events(messages, *, model, settings=None, ollama_client=None):
        yield {"type": "status", "stage": "started", "model": model, "timeout_s": 120}
        yield {
            "type": "graph",
            "node": "input_node",
            "phase": "completed",
            "detail": "Prepared prompt messages.",
            "timestamp": "2026-04-03T15:00:00+00:00",
        }
        yield {"type": "token", "content": "Hello"}
        yield {
            "type": "done",
            "result": {
                "input": "Hi",
                "model": model,
                "response": "Hello",
                "timestamp": "2026-04-03T15:00:00+00:00",
                "metrics": {"word_count": 1, "char_count": 5, "latency_ms": 5.0},
            },
        }

    monkeypatch.setattr(api_module, "stream_chat_events", fake_stream_chat_events)

    with client.stream(
        "POST",
        "/stream",
        json={"prompt": "Hi", "model": "phi4-mini"},
    ) as response:
        lines = [line for line in response.iter_lines() if line]

    assert response.status_code == 200
    assert "application/x-ndjson" in response.headers["content-type"]
    assert lines[0] == '{"type": "status", "stage": "started", "model": "phi4-mini", "timeout_s": 120}'
    assert '"type": "graph"' in lines[1]
    assert lines[2] == '{"type": "token", "content": "Hello"}'
    assert '"type": "done"' in lines[3]
