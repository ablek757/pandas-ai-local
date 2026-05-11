"""End-to-end agent test using a stub provider — no API key needed."""

from __future__ import annotations

import pandas as pd

from nlda.agent import AnalysisAgent
from nlda.config import Config
from nlda.loaders.profile import profile_dataframe
from nlda.providers.base import LLMProvider


class _StubGood(LLMProvider):
    name = "stub"

    def complete(self, system, messages, model, temperature=0.2, max_tokens=2048):
        return "```python\nresult = df['a'].sum()\n```"


class _StubBadThenGood(LLMProvider):
    name = "stub"

    def __init__(self):
        self.calls = 0

    def complete(self, system, messages, model, temperature=0.2, max_tokens=2048):
        self.calls += 1
        if self.calls == 1:
            return "```python\nresult = df['nope'].sum()\n```"
        return "```python\nresult = df['a'].sum()\n```"


def _make_agent(provider, df):
    agent = AnalysisAgent.__new__(AnalysisAgent)
    agent.config = Config(provider="stub", max_retries=2, exec_timeout=5.0)
    agent.provider = provider
    agent.dataframes = {"df": df}
    agent._profiles = {"df": profile_dataframe(df)}
    agent.session_id = "test"
    agent.turns = []
    return agent


def test_happy_path():
    df = pd.DataFrame({"a": [1, 2, 3]})
    agent = _make_agent(_StubGood(), df)
    turn = agent.ask("sum a")
    assert turn.error is None
    assert "6" in turn.result_repr


def test_retry_on_error():
    df = pd.DataFrame({"a": [1, 2, 3]})
    stub = _StubBadThenGood()
    agent = _make_agent(stub, df)
    turn = agent.ask("sum a")
    assert turn.error is None
    assert stub.calls == 2
    assert "6" in turn.result_repr


def test_session_save(tmp_path, monkeypatch):
    import nlda.agent as agent_mod

    monkeypatch.setattr(agent_mod, "SESSIONS_DIR", tmp_path)
    df = pd.DataFrame({"a": [1, 2, 3]})
    agent = _make_agent(_StubGood(), df)
    agent.ask("sum a")
    path = agent.save_session()
    assert path.exists()
    assert "sum a" in path.read_text(encoding="utf-8")
