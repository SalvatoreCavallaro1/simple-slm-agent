from __future__ import annotations

import json
import logging
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from starlette.staticfiles import StaticFiles

from .config import load_settings
from .logging_config import configure_logging
from .model_registry import get_model
from .ollama_client import OllamaClientError, OllamaTimeoutError
from .prompts import normalize_conversation
from .runner import run_prompt
from .streaming import stream_chat_events

logger = logging.getLogger(__name__)
settings = load_settings()
configure_logging(settings.log_level)
static_dir = Path(__file__).resolve().parent / "static"

app = FastAPI(title="slm-langgraph-playground", version="0.1.0")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1)


class RunRequest(BaseModel):
    prompt: str | None = None
    messages: list[ConversationMessage] | None = None
    model: str | None = None


def _model_dump(instance: BaseModel) -> dict[str, Any]:
    dump = getattr(instance, "model_dump", None)
    if callable(dump):
        return dump()
    return instance.dict()


def _request_messages(request: RunRequest) -> list[dict[str, Any]] | None:
    if not request.messages:
        return None
    return [_model_dump(message) for message in request.messages]


def _stream_ndjson(events: Iterable[dict[str, Any]]) -> Iterator[str]:
    for event in events:
        yield json.dumps(event, ensure_ascii=True) + "\n"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/chat")
def chat() -> FileResponse:
    return FileResponse(static_dir / "chat.html")


@app.get("/chat/config")
def chat_config() -> dict[str, Any]:
    return {
        "title": app.title,
        "primary_model": settings.primary_model,
        "available_models": list(settings.available_models),
        "request_timeout_s": settings.request_timeout_s,
    }


@app.post("/run")
def run(request: RunRequest) -> dict[str, Any]:
    messages = _request_messages(request)

    try:
        return run_prompt(
            request.prompt,
            model=request.model,
            messages=messages,
            settings=settings,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OllamaTimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except OllamaClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("API execution failed")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@app.post("/stream")
def stream(request: RunRequest) -> StreamingResponse:
    messages = _request_messages(request)

    try:
        conversation = normalize_conversation(prompt=request.prompt, messages=messages)
        selected_model = get_model(request.model, settings)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return StreamingResponse(
        _stream_ndjson(
            stream_chat_events(
                conversation,
                model=selected_model,
                settings=settings,
            )
        ),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
