from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import load_settings
from .logging_config import configure_logging
from .runner import run_prompt

logger = logging.getLogger(__name__)
settings = load_settings()
configure_logging(settings.log_level)

app = FastAPI(title="slm-langgraph-playground", version="0.1.0")


class RunRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    model: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run")
def run(request: RunRequest) -> dict[str, Any]:
    try:
        return run_prompt(request.prompt, model=request.model, settings=settings)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("API execution failed")
        raise HTTPException(status_code=500, detail="Internal server error") from exc
