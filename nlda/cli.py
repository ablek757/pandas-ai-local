"""Typer-based command line interface."""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from .agent import AnalysisAgent
from .config import load_config
from .loaders import load_path, load_sql
from .report import to_html, to_markdown

app = typer.Typer(add_completion=False, help="Natural-language data analysis on your terminal.")
console = Console()


@app.command()
def chat(
    source: str = typer.Argument(..., help="CSV/Excel/Parquet/JSON path, OR sql://<conn>::<query|table>"),
    provider: str | None = typer.Option(None, "--provider", "-p", help="claude | openai | ollama"),
    model: str | None = typer.Option(None, "--model", "-m"),
    name: str = typer.Option("df", "--name", help="Variable name exposed to the LLM."),
) -> None:
    """Start an interactive chat over a data source."""
    cfg = load_config({"provider": provider, "model": model})
    df = _load_source(source)
    console.print(Panel.fit(
        f"Loaded `{name}` — {df.shape[0]} rows x {df.shape[1]} cols\n"
        f"Provider: {cfg.provider}  Model: {cfg.resolved_model()}",
        title="nlda",
    ))

    agent = AnalysisAgent(cfg, {name: df})

    while True:
        try:
            q = console.input("[bold cyan]you[/]> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            break
        if not q:
            continue
        if q.startswith("/"):
            if _handle_command(agent, q):
                break
            continue

        with console.status("[dim]thinking...[/]"):
            turn = agent.ask(q)

        console.print(Panel(Syntax(turn.code, "python", theme="monokai", word_wrap=True), title="code"))
        if turn.error:
            console.print(f"[red]error:[/] {turn.error}")
        if turn.stdout.strip():
            console.print(Panel(turn.stdout.rstrip(), title="stdout"))
        if turn.result_repr.strip():
            console.print(Panel(turn.result_repr, title="result"))
        if turn.figures:
            console.print(f"[green]{len(turn.figures)} figure(s) captured — save with `/save report.md`[/]")


def _handle_command(agent: AnalysisAgent, line: str) -> bool:
    """Return True to break the chat loop."""
    parts = line.split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd in {"/quit", "/exit", "/q"}:
        path = agent.save_session()
        console.print(f"[dim]session saved → {path}[/]")
        return True
    if cmd == "/save":
        if not arg:
            console.print("usage: /save <path.md|path.html>")
            return False
        out = Path(arg)
        if out.suffix.lower() == ".html":
            out.write_text(to_html(agent), encoding="utf-8")
        else:
            out.write_text(to_markdown(agent), encoding="utf-8")
        console.print(f"[green]report saved → {out}[/]")
        return False
    if cmd == "/profile":
        console.print(Panel(agent.profile_text(), title="profile"))
        return False
    if cmd == "/history":
        tbl = Table("#", "question", "ok")
        for i, t in enumerate(agent.turns, 1):
            tbl.add_row(str(i), t.question, "✓" if not t.error else "✗")
        console.print(tbl)
        return False
    if cmd == "/help":
        console.print("/save <file>   /profile   /history   /quit")
        return False
    console.print(f"[red]unknown command:[/] {cmd}")
    return False


def _load_source(source: str):
    if source.startswith("sql://"):
        body = source[len("sql://"):]
        if "::" not in body:
            console.print("[red]sql source must be: sql://<conn>::<query_or_table>[/]")
            sys.exit(2)
        conn, q = body.split("::", 1)
        return load_sql(conn, q)
    return load_path(source)


@app.command()
def web(
    host: str = typer.Option("localhost", "--host"),
    port: int = typer.Option(8501, "--port"),
) -> None:
    """Launch the Streamlit web UI."""
    import subprocess

    ui_path = Path(__file__).parent / "ui" / "streamlit_app.py"
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(ui_path),
         "--server.address", host, "--server.port", str(port)],
        check=False,
    )


@app.command()
def config() -> None:
    """Show effective configuration (secrets redacted)."""
    cfg = load_config()
    for k, v in cfg.as_dict().items():
        console.print(f"  {k} = {v}")


if __name__ == "__main__":
    app()
