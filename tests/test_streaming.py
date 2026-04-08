from __future__ import annotations

from app.config import Settings
from app.streaming import stream_chat_events


class FakeStreamingOllamaClient:
    timeout_s = 45

    def stream_chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0,
    ):
        assert model == "phi4-mini"
        assert messages[0]["role"] == "system"
        assert temperature == 0
        yield "Hel"
        yield "lo"


def test_stream_chat_events_uses_langgraph_debug_events() -> None:
    settings = Settings(
        primary_model="phi4-mini",
        available_models=("phi4-mini",),
        request_timeout_s=45,
    )

    events = list(
        stream_chat_events(
            [{"role": "user", "content": "Hi"}],
            model="phi4-mini",
            settings=settings,
            ollama_client=FakeStreamingOllamaClient(),
        )
    )

    assert events[0] == {
        "type": "status",
        "stage": "started",
        "model": "phi4-mini",
        "timeout_s": 45,
    }

    graph_nodes = [event["node"] for event in events if event.get("type") == "graph"]
    assert "input_node" in graph_nodes
    assert "model_node" in graph_nodes
    assert "evaluator_node" in graph_nodes

    token_events = [event for event in events if event.get("type") == "token"]
    assert token_events == [
        {"type": "token", "content": "Hel"},
        {"type": "token", "content": "lo"},
    ]

    assert events[-1]["type"] == "done"
    assert events[-1]["result"]["response"] == "Hello"
