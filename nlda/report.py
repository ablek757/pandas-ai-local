"""Export an agent session to Markdown or self-contained HTML."""

from __future__ import annotations

import base64
import html
from pathlib import Path

from .agent import AnalysisAgent


def to_markdown(agent: AnalysisAgent, image_dir: Path | None = None) -> str:
    lines: list[str] = []
    lines.append(f"# Analysis report — session `{agent.session_id}`")
    lines.append("")
    lines.append(f"- Provider: `{agent.config.provider}`")
    lines.append(f"- Model: `{agent.config.resolved_model()}`")
    lines.append(f"- Dataframes: {', '.join(f'`{n}`' for n in agent.dataframes)}")
    lines.append("")
    lines.append("## Data profile")
    lines.append("```")
    lines.append(agent.profile_text())
    lines.append("```")

    for i, t in enumerate(agent.turns, 1):
        lines.append("")
        lines.append(f"## Q{i}. {t.question}")
        lines.append("")
        lines.append("```python")
        lines.append(t.code)
        lines.append("```")
        if t.error:
            lines.append("")
            lines.append(f"**Error:** {t.error}")
        if t.stdout.strip():
            lines.append("")
            lines.append("Output:")
            lines.append("```")
            lines.append(t.stdout.rstrip())
            lines.append("```")
        if t.result_repr.strip():
            lines.append("")
            lines.append("Result:")
            lines.append("```")
            lines.append(t.result_repr)
            lines.append("```")
        for j, fig in enumerate(t.figures, 1):
            if image_dir is not None:
                image_dir.mkdir(parents=True, exist_ok=True)
                fname = f"{agent.session_id}_q{i}_f{j}.png"
                (image_dir / fname).write_bytes(fig)
                lines.append("")
                lines.append(f"![figure {i}.{j}]({fname})")
            else:
                b64 = base64.b64encode(fig).decode()
                lines.append("")
                lines.append(f"![figure {i}.{j}](data:image/png;base64,{b64})")
    return "\n".join(lines)


def to_html(agent: AnalysisAgent) -> str:
    body_parts: list[str] = [
        f"<h1>Analysis report — {html.escape(agent.session_id)}</h1>",
        f"<p>Provider: <code>{html.escape(agent.config.provider)}</code><br>",
        f"Model: <code>{html.escape(agent.config.resolved_model())}</code></p>",
        "<h2>Data profile</h2>",
        f"<pre>{html.escape(agent.profile_text())}</pre>",
    ]
    for i, t in enumerate(agent.turns, 1):
        body_parts.append(f"<h2>Q{i}. {html.escape(t.question)}</h2>")
        body_parts.append(f"<pre><code>{html.escape(t.code)}</code></pre>")
        if t.error:
            body_parts.append(f"<p><b>Error:</b> {html.escape(t.error)}</p>")
        if t.stdout.strip():
            body_parts.append(f"<pre>{html.escape(t.stdout)}</pre>")
        if t.result_repr.strip():
            body_parts.append(f"<pre>{html.escape(t.result_repr)}</pre>")
        for fig in t.figures:
            b64 = base64.b64encode(fig).decode()
            body_parts.append(f'<img src="data:image/png;base64,{b64}" />')

    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>nlda report</title>"
        "<style>body{font-family:sans-serif;max-width:880px;margin:2em auto;padding:0 1em}"
        "pre{background:#f4f4f4;padding:0.7em;overflow:auto}"
        "img{max-width:100%}</style></head><body>"
        + "".join(body_parts)
        + "</body></html>"
    )
