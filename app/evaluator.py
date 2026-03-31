from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def evaluate_response(
    *,
    input_text: str,
    model: str,
    response: str,
    latency_ms: float,
) -> dict[str, Any]:
    cleaned_response = response.strip()

    return {
        "input": input_text,
        "model": model,
        "response": cleaned_response,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "metrics": {
            "word_count": len(cleaned_response.split()),
            "char_count": len(cleaned_response),
            "latency_ms": round(latency_ms, 3),
        },
    }
