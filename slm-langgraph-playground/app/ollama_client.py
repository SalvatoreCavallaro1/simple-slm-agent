from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import requests

from .config import Settings, load_settings


class OllamaClientError(RuntimeError):
    """Raised when the local Ollama API request fails."""


@dataclass(slots=True)
class OllamaClient:
    host: str
    port: int
    timeout_s: int = 120
    session: requests.Session = field(default_factory=requests.Session)

    def __post_init__(self) -> None:
        self.host = self._validate_host(self.host)

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "OllamaClient":
        runtime_settings = settings or load_settings()
        return cls(
            host=runtime_settings.ollama_host,
            port=runtime_settings.ollama_port,
            timeout_s=runtime_settings.request_timeout_s,
        )

    @staticmethod
    def _validate_host(host: str) -> str:
        normalized_host = host.strip()

        if "://" in normalized_host:
            parsed = urlparse(normalized_host)
            normalized_host = parsed.hostname or ""

        if normalized_host not in {"localhost", "127.0.0.1"}:
            raise ValueError("Ollama host must be localhost or 127.0.0.1.")

        return normalized_host

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0,
    ) -> str:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout_s,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise OllamaClientError(f"Failed to reach local Ollama at {self.base_url}.") from exc

        data = response.json()
        message = data.get("message")
        content = message.get("content") if isinstance(message, dict) else None

        if not isinstance(content, str):
            raise OllamaClientError("Ollama response did not include message.content.")

        return content
