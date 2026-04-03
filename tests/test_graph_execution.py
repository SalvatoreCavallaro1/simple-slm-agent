from __future__ import annotations

from app.config import Settings
from app.graph import run_graph
from app.prompts import SYSTEM_PROMPT


class FakeOllamaClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0,
    ) -> str:
        self.calls.append(
            {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
        )
        return "An API gateway routes, secures, and manages API traffic."


def test_graph_runs_and_returns_expected_keys() -> None:
    settings = Settings(
        primary_model="phi4-mini",
        available_models=("phi4-mini", "qwen3:4b"),
    )
    client = FakeOllamaClient()

    result = run_graph(
        "Explain what an API gateway is",
        settings=settings,
        ollama_client=client,
    )

    assert result["input"] == "Explain what an API gateway is"
    assert result["model"] == "phi4-mini"
    assert "response" in result
    assert "timestamp" in result
    assert result["metrics"]["word_count"] > 0
    assert result["metrics"]["char_count"] == len(result["response"])
    assert result["metrics"]["latency_ms"] >= 0
    assert client.calls[0]["temperature"] == 0


def test_graph_preserves_multi_turn_history() -> None:
    settings = Settings(
        primary_model="phi4-mini",
        available_models=("phi4-mini", "qwen3:4b"),
    )
    client = FakeOllamaClient()
    conversation = [
        {"role": "user", "content": "Hello there"},
        {"role": "assistant", "content": "Hi, what do you need?"},
        {"role": "user", "content": "Explain what an API gateway is"},
    ]

    result = run_graph(
        messages=conversation,
        settings=settings,
        ollama_client=client,
    )

    assert result["input"] == "Explain what an API gateway is"
    assert client.calls[0]["messages"] == [
        {"role": "system", "content": SYSTEM_PROMPT},
        *conversation,
    ]
