"""Run a single offline question against the bundled sample CSV.

This script uses a stub provider so it works WITHOUT any API keys — useful
for verifying installation. For real analysis use `nlda chat ...`.
"""

from __future__ import annotations

from pathlib import Path

from nlda.agent import AnalysisAgent
from nlda.config import Config
from nlda.loaders import load_path
from nlda.providers.base import LLMProvider, Message


class StubProvider(LLMProvider):
    name = "stub"

    def complete(self, system, messages, model, temperature=0.2, max_tokens=2048):
        return (
            "```python\n"
            "result = df.groupby('product')['units'].sum().sort_values(ascending=False)\n"
            "```"
        )


def main() -> None:
    df = load_path(Path(__file__).parent / "data" / "sales.csv")
    cfg = Config(provider="stub")

    agent = AnalysisAgent.__new__(AnalysisAgent)
    agent.config = cfg
    agent.provider = StubProvider()
    agent.dataframes = {"df": df}
    from nlda.loaders.profile import profile_dataframe
    agent._profiles = {"df": profile_dataframe(df)}
    agent.session_id = "demo"
    agent.turns = []

    turn = agent.ask("Total units per product, descending.")
    print("CODE:")
    print(turn.code)
    print("\nRESULT:")
    print(turn.result_repr)


if __name__ == "__main__":
    main()
