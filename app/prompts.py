from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypedDict

SYSTEM_PROMPT = (
    "You are a concise assistant in a local model playground. "
    "Respond clearly, directly, and keep the answer easy to inspect."
)
ALLOWED_MESSAGE_ROLES = frozenset({"user", "assistant"})


class ChatMessage(TypedDict):
    role: str
    content: str


def _normalize_message(message: Mapping[str, object], *, index: int) -> ChatMessage:
    role = message.get("role")
    content = message.get("content")

    if not isinstance(role, str) or role.strip().lower() not in ALLOWED_MESSAGE_ROLES:
        raise ValueError("Conversation messages must use role 'user' or 'assistant'.")

    if not isinstance(content, str) or not content.strip():
        raise ValueError(f"Conversation message {index + 1} must include non-empty content.")

    return {
        "role": role.strip().lower(),
        "content": content.strip(),
    }


def normalize_conversation(
    *,
    prompt: str | None = None,
    messages: Sequence[Mapping[str, object]] | None = None,
) -> list[ChatMessage]:
    if prompt is not None and messages is not None:
        raise ValueError("Provide either 'prompt' or 'messages', not both.")

    if messages is not None:
        conversation = [_normalize_message(message, index=index) for index, message in enumerate(messages)]
    elif prompt is not None and prompt.strip():
        conversation = [{"role": "user", "content": prompt.strip()}]
    else:
        raise ValueError("Request must include a non-empty 'prompt' or a non-empty 'messages' list.")

    if not any(message["role"] == "user" for message in conversation):
        raise ValueError("Conversation must include at least one user message.")

    return conversation


def extract_latest_user_message(messages: Sequence[Mapping[str, str]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return message["content"].strip()

    raise ValueError("Conversation must include at least one user message.")


def build_messages(
    *,
    prompt: str | None = None,
    messages: Sequence[Mapping[str, object]] | None = None,
) -> list[ChatMessage]:
    conversation = normalize_conversation(prompt=prompt, messages=messages)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        *conversation,
    ]
