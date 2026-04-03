from __future__ import annotations

from app.config import load_settings


def test_load_settings_reads_langfuse_project_name(monkeypatch) -> None:
    monkeypatch.setenv("LANGFUSE_PROJECT_NAME", "simple-slm-agent")

    settings = load_settings()

    assert settings.langfuse_project_name == "simple-slm-agent"


def test_load_settings_supports_langfuse_base_url_alias(monkeypatch) -> None:
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    monkeypatch.setenv("LANGFUSE_BASE_URL", "https://self-hosted.langfuse.local")

    settings = load_settings()

    assert settings.langfuse_host == "https://self-hosted.langfuse.local"


def test_load_settings_strips_wrapping_quotes_from_env(monkeypatch) -> None:
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", '"pk-test"')
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "'sk-test'")
    monkeypatch.setenv("OLLAMA_PORT", '"11435"')
    monkeypatch.setenv("REQUEST_TIMEOUT_S", '"240"')

    settings = load_settings()

    assert settings.langfuse_public_key == "pk-test"
    assert settings.langfuse_secret_key == "sk-test"
    assert settings.ollama_port == 11435
    assert settings.request_timeout_s == 240
