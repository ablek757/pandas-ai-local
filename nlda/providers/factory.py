from __future__ import annotations

from ..config import Config
from .base import LLMProvider


def get_provider(cfg: Config) -> LLMProvider:
    name = cfg.provider.lower()
    if name == "claude":
        from .claude import ClaudeProvider
        return ClaudeProvider(cfg.anthropic_api_key)
    if name == "openai":
        from .openai_provider import OpenAIProvider
        return OpenAIProvider(cfg.openai_api_key)
    if name == "ollama":
        from .ollama import OllamaProvider
        return OllamaProvider(cfg.ollama_base_url)
    raise ValueError(f"Unknown provider: {cfg.provider!r}. Use claude|openai|ollama.")
