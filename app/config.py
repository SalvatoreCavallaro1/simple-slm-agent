from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _clean_env_value(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None

    cleaned_value = raw_value.strip()
    if len(cleaned_value) >= 2 and cleaned_value[0] == cleaned_value[-1] and cleaned_value[0] in {"'", '"'}:
        cleaned_value = cleaned_value[1:-1].strip()

    return cleaned_value


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
    langfuse_project_name: str | None = None
    log_level: str = "INFO"
    request_timeout_s: int = 120

    @property
    def langfuse_enabled(self) -> bool:
        return bool(self.langfuse_public_key and self.langfuse_secret_key)


def load_settings() -> Settings:
    root_dir = Path(__file__).resolve().parents[1]
    env_path = root_dir / ".env"
    load_dotenv(env_path if env_path.exists() else None, override=False)

    primary_model = _clean_env_value(os.getenv("PRIMARY_MODEL")) or "phi4-mini"
    available_models = _parse_available_models(_clean_env_value(os.getenv("AVAILABLE_MODELS")), primary_model)

    public_key = _clean_env_value(os.getenv("LANGFUSE_PUBLIC_KEY")) or None
    secret_key = _clean_env_value(os.getenv("LANGFUSE_SECRET_KEY")) or None
    langfuse_host = (
        _clean_env_value(os.getenv("LANGFUSE_HOST"))
        or _clean_env_value(os.getenv("LANGFUSE_BASE_URL"))
        or "https://cloud.langfuse.com"
    )
    langfuse_project_name = _clean_env_value(os.getenv("LANGFUSE_PROJECT_NAME")) or None
    log_level = (_clean_env_value(os.getenv("LOG_LEVEL")) or "INFO").upper()
    ollama_host = _clean_env_value(os.getenv("OLLAMA_HOST")) or "127.0.0.1"
    ollama_port = int(_clean_env_value(os.getenv("OLLAMA_PORT")) or "11434")

    return Settings(
        ollama_host=ollama_host,
        ollama_port=ollama_port,
        primary_model=primary_model,
        available_models=available_models,
        langfuse_public_key=public_key,
        langfuse_secret_key=secret_key,
        langfuse_host=langfuse_host,
        langfuse_project_name=langfuse_project_name,
        log_level=log_level,
    )
