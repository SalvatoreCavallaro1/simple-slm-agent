from __future__ import annotations

import logging
import time
from collections.abc import Iterator, Mapping, Sequence
from typing import Any

from .config import Settings, load_settings
from .evaluator import evaluate_response
from .ollama_client import OllamaClient, OllamaClientError, OllamaTimeoutError
from .prompts import build_messages, extract_latest_user_message

logger = logging.getLogger(__name__)


def stream_chat_events(
    messages: Sequence[Mapping[str, str]],
    *,
    model: str,
    settings: Settings | None = None,
    ollama_client: OllamaClient | None = None,
) -> Iterator[dict[str, Any]]:
    runtime_settings = settings or load_settings()
    client = ollama_client or OllamaClient.from_settings(runtime_settings)
    prompt_messages = build_messages(messages=messages)
    latest_user_input = extract_latest_user_message(messages)
    started_at = time.perf_counter()
    collected_chunks: list[str] = []

    yield {
        "type": "status",
        "stage": "started",
        "model": model,
        "timeout_s": client.timeout_s,
    }

    try:
        for chunk in client.stream_chat(
            model=model,
            messages=prompt_messages,
            temperature=0,
        ):
            collected_chunks.append(chunk)
            yield {"type": "token", "content": chunk}
    except OllamaTimeoutError as exc:
        logger.warning(
            "Streaming model call timed out",
            extra={"graph_node": "streaming", "model": model},
        )
        yield {"type": "error", "code": "timeout", "detail": str(exc)}
        return
    except OllamaClientError as exc:
        logger.warning(
            "Streaming model call failed",
            extra={"graph_node": "streaming", "model": model},
        )
        yield {"type": "error", "code": "ollama_error", "detail": str(exc)}
        return
    except Exception:
        logger.exception(
            "Streaming execution failed",
            extra={"graph_node": "streaming", "model": model},
        )
        yield {
            "type": "error",
            "code": "internal_error",
            "detail": "Streaming execution failed.",
        }
        return

    result = evaluate_response(
        input_text=latest_user_input,
        model=model,
        response="".join(collected_chunks),
        latency_ms=(time.perf_counter() - started_at) * 1000,
    )
    logger.info(
        "Streaming response completed",
        extra={
            "graph_node": "streaming",
            "model": model,
            "latency_ms": result["metrics"]["latency_ms"],
        },
    )
    yield {"type": "done", "result": result}
