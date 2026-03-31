from __future__ import annotations

import os

from .config import Settings, load_settings


def list_models(settings: Settings | None = None) -> tuple[str, ...]:
    runtime_settings = settings or load_settings()
    return runtime_settings.available_models


def get_model(name: str | None, settings: Settings | None = None) -> str:
    runtime_settings = settings or load_settings()
    candidate = (name or os.getenv("MODEL") or runtime_settings.primary_model).strip()

    if candidate not in runtime_settings.available_models:
        available_models = ", ".join(runtime_settings.available_models)
        raise ValueError(
            f"Model '{candidate}' is not in AVAILABLE_MODELS. Available models: {available_models}"
        )

    return candidate
