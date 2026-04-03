from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any

from langfuse import Langfuse

from .config import Settings, load_settings
from .graph import run_graph
from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)


def create_langfuse_client(settings: Settings) -> Langfuse | None:
    if not settings.langfuse_enabled:
        return None

    try:
        return Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            base_url=settings.langfuse_host,
        )
    except Exception:
        logger.exception("Failed to initialize Langfuse; continuing without tracing.")
        return None


def _flush_langfuse(client: Langfuse | None) -> None:
    if client is None:
        return

    flush = getattr(client, "flush", None)
    if callable(flush):
        flush()


def run_prompt(
    prompt: str | None = None,
    *,
    model: str | None = None,
    messages: Sequence[Mapping[str, object]] | None = None,
    settings: Settings | None = None,
    ollama_client: OllamaClient | None = None,
) -> dict[str, Any]:
    runtime_settings = settings or load_settings()
    langfuse_client = create_langfuse_client(runtime_settings)

    try:
        result = run_graph(
            prompt,
            model=model,
            messages=messages,
            settings=runtime_settings,
            ollama_client=ollama_client,
            langfuse_client=langfuse_client,
        )
        logger.info(
            "Graph execution finished",
            extra={
                "graph_node": "runner",
                "model": result["model"],
                "latency_ms": result["metrics"]["latency_ms"],
            },
        )
        return result
    finally:
        _flush_langfuse(langfuse_client)
