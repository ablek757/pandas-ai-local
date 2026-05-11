"""Analysis agent: combines a provider, dataframes, and a conversation."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .config import Config, SESSIONS_DIR
from .loaders.profile import profile_dataframe, render_profile_text
from .parsing import extract_code
from .prompts import SYSTEM_PROMPT, build_retry_prompt, build_user_prompt
from .providers import Message, get_provider
from .sandbox import ExecResult, run_code


@dataclass
class Turn:
    question: str
    code: str
    stdout: str
    result_repr: str
    figures: list[bytes] = field(default_factory=list)
    error: str | None = None
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AnalysisAgent:
    def __init__(
        self,
        config: Config,
        dataframes: dict[str, pd.DataFrame],
        session_id: str | None = None,
    ):
        if not dataframes:
            raise ValueError("At least one dataframe is required.")
        self.config = config
        self.provider = get_provider(config)
        self.dataframes = dataframes
        self._profiles = {
            name: profile_dataframe(df) for name, df in dataframes.items()
        }
        self.session_id = session_id or _new_session_id()
        self.turns: list[Turn] = []

    @property
    def primary_name(self) -> str:
        return next(iter(self.dataframes))

    def profile_text(self) -> str:
        return render_profile_text(self._profiles[self.primary_name])

    def ask(self, question: str) -> Turn:
        df_names = list(self.dataframes.keys())
        user_prompt = build_user_prompt(self.profile_text(), df_names, question)

        messages: list[Message] = []
        for t in self.turns:
            messages.append(Message("user", t.question))
            messages.append(Message("assistant", f"```python\n{t.code}\n```"))
        messages.append(Message("user", user_prompt))

        code, exec_result = self._generate_and_run(messages)

        for attempt in range(self.config.max_retries):
            if exec_result.ok:
                break
            messages.append(Message("assistant", f"```python\n{code}\n```"))
            messages.append(Message("user", build_retry_prompt(code, exec_result.error or "")))
            code, exec_result = self._generate_and_run(messages)

        turn = Turn(
            question=question,
            code=code,
            stdout=exec_result.stdout,
            result_repr=_repr_result(exec_result.result),
            figures=exec_result.figures,
            error=exec_result.error,
        )
        self.turns.append(turn)
        return turn

    def _generate_and_run(self, messages: list[Message]) -> tuple[str, ExecResult]:
        raw = self.provider.complete(
            system=SYSTEM_PROMPT,
            messages=messages,
            model=self.config.resolved_model(),
            temperature=self.config.temperature,
        )
        code = extract_code(raw)
        result = run_code(code, self.dataframes, timeout=self.config.exec_timeout)
        return code, result

    def save_session(self) -> Path:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        path = SESSIONS_DIR / f"{self.session_id}.json"
        payload = {
            "session_id": self.session_id,
            "provider": self.config.provider,
            "model": self.config.resolved_model(),
            "dataframes": list(self.dataframes.keys()),
            "profiles": self._profiles,
            "turns": [
                {
                    "question": t.question,
                    "code": t.code,
                    "stdout": t.stdout,
                    "result_repr": t.result_repr,
                    "error": t.error,
                    "ts": t.ts,
                    "figure_count": len(t.figures),
                }
                for t in self.turns
            ],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return path


def _new_session_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]


def _repr_result(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, pd.DataFrame):
        return value.head(20).to_string()
    if isinstance(value, pd.Series):
        return value.head(20).to_string()
    return repr(value)
