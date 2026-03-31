from __future__ import annotations

from app.config import load_settings


def test_load_settings_reads_langfuse_project_name(monkeypatch) -> None:
    monkeypatch.setenv("LANGFUSE_PROJECT_NAME", "simple-slm-agent")

    settings = load_settings()

    assert settings.langfuse_project_name == "simple-slm-agent"
