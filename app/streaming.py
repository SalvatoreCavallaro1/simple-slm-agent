from __future__ import annotations

import logging
import time
from collections.abc import Iterator, Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from .config import Settings, load_settings
from .graph import build_graph
from .model_registry import get_model
from .ollama_client import OllamaClient, OllamaClientError, OllamaTimeoutError
from .prompts import extract_latest_user_message, normalize_conversation

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _summarize_node_update(result: Any) -> str:
    if isinstance(result, dict) and result:
        keys = ", ".join(sorted(str(key) for key in result))
        return f"State updated: {keys}."
    if result is None:
        return "Node completed without state changes."
    return "Node completed."


def _graph_event_from_debug(event: dict[str, Any]) -> dict[str, Any] | None:
    event_type = event.get("type")
    payload = event.get("payload")
    timestamp = event.get("timestamp")

    if not isinstance(payload, dict):
        return None

    node_name = payload.get("name")
    if not isinstance(node_name, str):
        return None

    if event_type == "task":
        return {
            "type": "graph",
            "node": node_name,
            "phase": "running",
            "detail": "Node started.",
            "timestamp": timestamp,
        }

    if event_type != "task_result":
        return None

    error = payload.get("error")
    if error is not None:
        return {
            "type": "graph",
            "node": node_name,
            "phase": "failed",
            "detail": str(error),
            "timestamp": timestamp,
        }

    return {
        "type": "graph",
        "node": node_name,
        "phase": "completed",
        "detail": _summarize_node_update(payload.get("result")),
        "timestamp": timestamp,
    }


def stream_chat_events(
    messages: Sequence[Mapping[str, object]],
    *,
    model: str,
    settings: Settings | None = None,
    ollama_client: OllamaClient | None = None,
) -> Iterator[dict[str, Any]]:
    runtime_settings = settings or load_settings()
    conversation = normalize_conversation(messages=messages)
    selected_model = get_model(model, runtime_settings)
    latest_user_input = extract_latest_user_message(conversation)
    client = ollama_client or OllamaClient.from_settings(runtime_settings)
    graph = build_graph(client, runtime_settings)

    yield {
        "type": "status",
        "stage": "started",
        "model": selected_model,
        "timeout_s": client.timeout_s,
    }

    final_result: dict[str, Any] | None = None
    active_node: str | None = None

    try:
        for mode, payload in graph.stream(
            {
                "input": latest_user_input,
                "model": selected_model,
                "conversation": conversation,
                "stream_tokens": True,
                "started_at": time.perf_counter(),
            },
            stream_mode=["debug", "custom", "values"],
        ):
            if mode == "debug" and isinstance(payload, dict):
                graph_event = _graph_event_from_debug(payload)
                if graph_event is not None:
                    if graph_event["phase"] == "running":
                        active_node = graph_event["node"]
                    elif active_node == graph_event["node"]:
                        active_node = None
                    yield graph_event
                continue

            if mode == "custom" and isinstance(payload, dict):
                yield payload
                continue

            if mode == "values" and isinstance(payload, dict):
                candidate_result = payload.get("result")
                if isinstance(candidate_result, dict):
                    final_result = candidate_result
    except OllamaTimeoutError as exc:
        if active_node is not None:
            yield {
                "type": "graph",
                "node": active_node,
                "phase": "failed",
                "detail": str(exc),
                "timestamp": _utc_now(),
            }
        logger.warning(
            "Streaming model call timed out",
            extra={"graph_node": "streaming", "model": selected_model},
        )
        yield {"type": "error", "code": "timeout", "detail": str(exc)}
        return
    except OllamaClientError as exc:
        if active_node is not None:
            yield {
                "type": "graph",
                "node": active_node,
                "phase": "failed",
                "detail": str(exc),
                "timestamp": _utc_now(),
            }
        logger.warning(
            "Streaming model call failed",
            extra={"graph_node": "streaming", "model": selected_model},
        )
        yield {"type": "error", "code": "ollama_error", "detail": str(exc)}
        return
    except Exception:
        if active_node is not None:
            yield {
                "type": "graph",
                "node": active_node,
                "phase": "failed",
                "detail": "Graph execution failed.",
                "timestamp": _utc_now(),
            }
        logger.exception(
            "Streaming execution failed",
            extra={"graph_node": "streaming", "model": selected_model},
        )
        yield {
            "type": "error",
            "code": "internal_error",
            "detail": "Streaming execution failed.",
        }
        return

    if final_result is None:
        yield {
            "type": "error",
            "code": "internal_error",
            "detail": "Graph execution finished without a final result.",
        }
        return

    yield {"type": "done", "result": final_result}
