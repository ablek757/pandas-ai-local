# pandas-ai-local

> [中文](./README.md) · **English**

Natural-language driven automated data analysis.
Upload a CSV / Excel / SQLite / MySQL table, ask a question in plain English (or 中文),
and get pandas-powered answers, charts, and reports — backed by Claude, OpenAI, or a
local Ollama model.

> Multi-backend LLM • CLI + Web UI • Auto data profiling • Multi-turn chat •
> Sandboxed code execution • Database connectors • Auto report generation •
> Persistent session history.

---

## Why

Doing data analysis usually means:

1. Looking at the columns.
2. Writing pandas / matplotlib boilerplate.
3. Iterating on charts.
4. Pasting results into a report.

`pandas-ai-local` collapses all of that into a chat box. You describe what you want,
the LLM writes the pandas code, a sandbox runs it, and you see the result —
including charts and a one-click exportable report.

Unlike SaaS-only tools, every backend is swappable: use Anthropic Claude, OpenAI,
or a fully **local** Ollama model — no data leaves your machine.

## Features

- **Multi-backend LLM** — `claude` / `openai` / `ollama`, switch via config or CLI flag.
- **Two front-ends** — a Typer CLI (`nlda chat`) and a Streamlit Web UI (`nlda web`).
- **Auto data profiling** — every loaded dataset is summarised (dtypes, nulls, ranges, top values) and the summary is fed to the LLM as context.
- **Multi-turn conversation** — the agent remembers earlier questions, dataframes, and results in the same session.
- **Sandboxed execution** — generated code runs in a restricted namespace with no `os`, `subprocess`, `open`, or network access.
- **Database connectors** — load tables directly from SQLite or MySQL with a connection string.
- **Auto-retry on errors** — if generated code raises, the traceback is fed back to the LLM for repair (configurable max tries).
- **Reports** — export the entire session as Markdown or self-contained HTML.
- **Session persistence** — every chat is saved as JSON under `~/.nlda/sessions/` and can be resumed.

## Architecture

```
┌─────────────┐  ┌─────────────┐
│   CLI       │  │  Streamlit  │
│ (Typer)     │  │   Web UI    │
└──────┬──────┘  └──────┬──────┘
       │                │
       └────────┬───────┘
                ▼
        ┌──────────────┐
        │  AnalysisAgent│   multi-turn chat, retry loop
        └──────┬───────┘
               │
   ┌───────────┼───────────────────┐
   ▼           ▼                   ▼
┌────────┐ ┌────────┐         ┌─────────────┐
│Provider│ │Loader  │         │   Sandbox   │
│(LLM)   │ │(data)  │         │ (exec code) │
└───┬────┘ └────────┘         └─────────────┘
    │
 ┌──┴──┬────────┬────────┐
 ▼     ▼        ▼        ▼
Claude OpenAI Ollama  (extensible)
```

## Quick start

```bash
git clone https://github.com/ablek757/pandas-ai-local.git
cd pandas-ai-local
pip install -e .
cp .env.example .env       # fill in keys you actually use
```

### CLI

```bash
nlda chat examples/data/sales.csv
> What are the top 5 products by revenue?
> Plot monthly revenue for 2024.
> Save report report.md
```

### Web UI

```bash
nlda web
# opens http://localhost:8501
```

### Pick a backend

```bash
nlda chat sales.csv --provider claude   --model claude-sonnet-4-6
nlda chat sales.csv --provider openai   --model gpt-4o-mini
nlda chat sales.csv --provider ollama   --model llama3.1
```

## Configuration

Configuration is layered (later overrides earlier):

1. defaults baked into the package
2. `~/.nlda/config.toml`
3. environment variables / `.env`
4. CLI flags

`.env.example`:

```
NLDA_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OLLAMA_BASE_URL=http://localhost:11434
```

## Safety

The sandbox:

- runs generated code in a fresh dict with only `pd`, `np`, `plt`, and the loaded dataframes;
- blocks `import os`, `import subprocess`, `open`, `eval`, `exec`, `__import__`, and dunder access via a static AST check;
- enforces a wall-clock timeout per execution.

This is **not** a security boundary against a determined attacker — treat the LLM
as untrusted *input* and run the tool on data you are willing to expose to your
chosen backend.

## Roadmap

- [ ] PDF report export
- [ ] DuckDB / Postgres connectors
- [ ] Chart-type recommender
- [ ] Caching of profiles + LLM calls

## License

MIT — see [LICENSE](LICENSE).
