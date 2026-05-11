# Contributing

Thanks for considering a contribution!

## Dev setup

```bash
git clone https://github.com/<you>/pandas-ai-local.git
cd pandas-ai-local
python -m venv .venv
. .venv/bin/activate   # or .venv\Scripts\Activate.ps1 on Windows
pip install -e ".[dev,all]"
pytest -q
```

## Project layout

- `nlda/providers/` — LLM backends (Claude, OpenAI, Ollama). Adding a new one
  means implementing `LLMProvider.complete` and wiring it into `factory.py`.
- `nlda/loaders/` — data loaders + profiling.
- `nlda/sandbox.py` — restricted executor for LLM-generated code.
- `nlda/agent.py` — orchestrates a conversation: profile → prompt → run → retry.
- `nlda/cli.py` — Typer CLI.
- `nlda/ui/streamlit_app.py` — Streamlit web UI.
- `tests/` — pytest suite; uses stub providers so no API keys are needed.

## Guidelines

- Keep changes minimal and focused. Prefer editing existing files over adding new ones.
- Run `pytest -q` before sending a PR.
- New features that talk to an external service must be covered by a test
  that uses a stub / mock — CI does not have API keys.
