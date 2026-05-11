from __future__ import annotations

import requests

from .base import LLMProvider, Message


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434"):
        self._base = base_url.rstrip("/")

    def complete(
        self,
        system: str,
        messages: list[Message],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        payload = {
            "model": model,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
            "messages": (
                [{"role": "system", "content": system}]
                + [{"role": m.role, "content": m.content} for m in messages]
            ),
        }
        r = requests.post(f"{self._base}/api/chat", json=payload, timeout=120)
        r.raise_for_status()
        return r.json().get("message", {}).get("content", "").strip()
