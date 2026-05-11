"""Layered configuration: defaults < ~/.nlda/config.toml < env / .env < CLI flags."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


HOME_DIR = Path.home() / ".nlda"
CONFIG_PATH = HOME_DIR / "config.toml"
SESSIONS_DIR = HOME_DIR / "sessions"


DEFAULT_MODELS = {
    "claude": "claude-sonnet-4-6",
    "openai": "gpt-4o-mini",
    "ollama": "llama3.1",
}


@dataclass
class Config:
    provider: str = "claude"
    model: str | None = None
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"
    max_retries: int = 2
    exec_timeout: float = 20.0
    temperature: float = 0.2

    def resolved_model(self) -> str:
        return self.model or DEFAULT_MODELS.get(self.provider, "")

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for k in ("anthropic_api_key", "openai_api_key"):
            if d.get(k):
                d[k] = "***"
        return d


def _from_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def _from_env() -> dict[str, Any]:
    load_dotenv(override=False)
    out: dict[str, Any] = {}
    if v := os.getenv("NLDA_PROVIDER"):
        out["provider"] = v
    if v := os.getenv("NLDA_MODEL"):
        out["model"] = v
    if v := os.getenv("ANTHROPIC_API_KEY"):
        out["anthropic_api_key"] = v
    if v := os.getenv("OPENAI_API_KEY"):
        out["openai_api_key"] = v
    if v := os.getenv("OLLAMA_BASE_URL"):
        out["ollama_base_url"] = v
    return out


def load_config(overrides: dict[str, Any] | None = None) -> Config:
    HOME_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    cfg = Config()
    for source in (_from_toml(CONFIG_PATH), _from_env(), overrides or {}):
        for k, v in source.items():
            if v is None:
                continue
            if hasattr(cfg, k):
                setattr(cfg, k, v)
    return cfg
