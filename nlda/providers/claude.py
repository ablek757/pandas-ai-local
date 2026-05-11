from __future__ import annotations

from .base import LLMProvider, Message


class ClaudeProvider(LLMProvider):
    name = "claude"

    def __init__(self, api_key: str | None):
        try:
            import anthropic
        except ImportError as e:
            raise RuntimeError(
                "anthropic package not installed. Run: pip install anthropic"
            ) from e
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set.")
        self._client = anthropic.Anthropic(api_key=api_key)

    def complete(
        self,
        system: str,
        messages: list[Message],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        resp = self._client.messages.create(
            model=model,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        parts = [b.text for b in resp.content if getattr(b, "type", "") == "text"]
        return "".join(parts).strip()
