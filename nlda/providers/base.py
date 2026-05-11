from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal


Role = Literal["system", "user", "assistant"]


@dataclass
class Message:
    role: Role
    content: str


class LLMProvider(ABC):
    """Minimal chat interface. All providers turn a message list into a string."""

    name: str = "base"

    @abstractmethod
    def complete(
        self,
        system: str,
        messages: list[Message],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str: ...
