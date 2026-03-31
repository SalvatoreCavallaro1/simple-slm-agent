from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _parse_available_models(raw_value: str | None, primary_model: str) -> tuple[str, ...]:
    if raw_value:
        parsed_models = tuple(model.strip() for model in raw_value.split(",") if model.strip())
    else:
        parsed_models = ()

    if not parsed_models:
        parsed_models = (primary_model,)

    if primary_model not in parsed_models:
        parsed_models = (primary_model, *parsed_models)

    return parsed_models


@dataclass(frozen=True, slots=True)
class Settings:
    ollama_host: str = "127.0.0.1"
    ollama_port: int = 11434
    primary_model: str = "phi4-mini"
    available_models: tuple[str, ...] = ("phi4-mini", "qwen3:4b", "llama3.2:3b")
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"
    log_level: str = "INFO"
    request_timeout_s: int = 120

    @property
    def langfuse_enabled(self) -> bool:
        return bool(self.langfuse_public_key and self.langfuse_secret_key)


def load_settings() -> Settings:
    root_dir = Path(__file__).resolve().parents[1]
    env_path = root_dir / ".env"
    load_dotenv(env_path if env_path.exists() else None, override=False)

    primary_model = os.getenv("PRIMARY_MODEL", "phi4-mini").strip() or "phi4-mini"
    available_models = _parse_available_models(os.getenv("AVAILABLE_MODELS"), primary_model)

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "").strip() or None
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "").strip() or None
    langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com").strip()
    log_level = os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO"

    return Settings(
        ollama_host=os.getenv("OLLAMA_HOST", "127.0.0.1").strip() or "127.0.0.1",
        ollama_port=int(os.getenv("OLLAMA_PORT", "11434")),
        primary_model=primary_model,
        available_models=available_models,
        langfuse_public_key=public_key,
        langfuse_secret_key=secret_key,
        langfuse_host=langfuse_host,
        log_level=log_level,
    )
