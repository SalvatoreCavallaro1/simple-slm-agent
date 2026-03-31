from __future__ import annotations

SYSTEM_PROMPT = (
    "You are a concise assistant in a local model playground. "
    "Respond clearly, directly, and keep the answer easy to inspect."
)


def build_messages(prompt: str) -> list[dict[str, str]]:
    cleaned_prompt = prompt.strip()
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": cleaned_prompt},
    ]
