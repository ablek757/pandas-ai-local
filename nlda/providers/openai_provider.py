from __future__ import annotations

from .base import LLMProvider, Message


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str | None):
        try:
            from openai import OpenAI
        except ImportError as e:
            raise RuntimeError(
                "openai package not installed. Run: pip install openai"
            ) from e
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        self._client = OpenAI(api_key=api_key)

    def complete(
        self,
        system: str,
        messages: list[Message],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        chat = [{"role": "system", "content": system}]
        chat += [{"role": m.role, "content": m.content} for m in messages]
        resp = self._client.chat.completions.create(
            model=model,
            messages=chat,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()
