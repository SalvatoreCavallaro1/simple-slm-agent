from __future__ import annotations

import pytest

from app.config import Settings
from app.graph import run_graph
from app.model_registry import get_model


class EchoOllamaClient:
    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0,
    ) -> str:
        return f"response from {model}"


@pytest.mark.parametrize("model_name", ["phi4-mini", "qwen3:4b"])
def test_graph_can_switch_models(model_name: str) -> None:
    settings = Settings(
        primary_model="phi4-mini",
        available_models=("phi4-mini", "qwen3:4b"),
    )

    result = run_graph(
        "Compare small language models",
        model=model_name,
        settings=settings,
        ollama_client=EchoOllamaClient(),
    )

    assert result["model"] == model_name
    assert model_name in result["response"]


def test_model_can_be_selected_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(
        primary_model="phi4-mini",
        available_models=("phi4-mini", "qwen3:4b"),
    )

    monkeypatch.setenv("MODEL", "qwen3:4b")

    assert get_model(None, settings) == "qwen3:4b"
