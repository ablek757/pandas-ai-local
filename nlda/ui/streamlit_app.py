"""Streamlit web UI for pandas-ai-local."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Allow `streamlit run` from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from nlda.agent import AnalysisAgent  # noqa: E402
from nlda.config import load_config  # noqa: E402
from nlda.loaders import load_path, load_sql  # noqa: E402
from nlda.report import to_html, to_markdown  # noqa: E402


st.set_page_config(page_title="nlda — natural-language data analyst", layout="wide")
st.title("📊 pandas-ai-local")
st.caption("Ask questions in plain language. Powered by Claude / OpenAI / Ollama.")


with st.sidebar:
    st.header("Backend")
    provider = st.selectbox("Provider", ["claude", "openai", "ollama"], index=0)
    model = st.text_input("Model (blank = default)", value="")
    st.divider()
    st.header("Data source")
    src_type = st.radio("Type", ["File upload", "File path", "SQL"], index=0)

    df: pd.DataFrame | None = None
    name = st.text_input("Variable name", value="df")

    if src_type == "File upload":
        up = st.file_uploader("CSV / Excel / Parquet / JSON", type=["csv", "xlsx", "xls", "parquet", "json"])
        if up is not None:
            suffix = Path(up.name).suffix.lower()
            try:
                if suffix == ".csv":
                    df = pd.read_csv(up)
                elif suffix in {".xlsx", ".xls"}:
                    df = pd.read_excel(up)
                elif suffix == ".parquet":
                    df = pd.read_parquet(up)
                elif suffix == ".json":
                    df = pd.read_json(up)
            except Exception as e:  # noqa: BLE001
                st.error(f"Failed to read file: {e}")
    elif src_type == "File path":
        path = st.text_input("Path on server", "")
        if path and Path(path).exists():
            try:
                df = load_path(path)
            except Exception as e:  # noqa: BLE001
                st.error(f"{e}")
    else:
        conn = st.text_input("Connection string", "sqlite:///example.db")
        query = st.text_area("Table name or SELECT ...", "")
        if conn and query:
            if st.button("Load"):
                try:
                    df = load_sql(conn, query)
                except Exception as e:  # noqa: BLE001
                    st.error(f"{e}")


def _ensure_agent(df: pd.DataFrame, name: str, provider: str, model: str) -> AnalysisAgent:
    cache_key = (id(df), name, provider, model)
    if st.session_state.get("agent_key") != cache_key:
        cfg = load_config({"provider": provider, "model": model or None})
        st.session_state.agent = AnalysisAgent(cfg, {name: df})
        st.session_state.agent_key = cache_key
        st.session_state.history = []
    return st.session_state.agent


if df is None:
    st.info("Load a dataset from the sidebar to get started.")
    st.stop()

agent = _ensure_agent(df, name, provider, model)

with st.expander("Preview & profile", expanded=False):
    st.dataframe(df.head(50), use_container_width=True)
    st.code(agent.profile_text())

st.divider()
for turn in st.session_state.get("history", []):
    with st.chat_message("user"):
        st.write(turn.question)
    with st.chat_message("assistant"):
        st.code(turn.code, language="python")
        if turn.error:
            st.error(turn.error)
        if turn.stdout.strip():
            st.text(turn.stdout)
        if turn.result_repr.strip():
            st.text(turn.result_repr)
        for fig in turn.figures:
            st.image(fig)

q = st.chat_input("Ask something about your data…")
if q:
    with st.chat_message("user"):
        st.write(q)
    with st.chat_message("assistant"), st.spinner("thinking…"):
        turn = agent.ask(q)
        st.session_state.history.append(turn)
        st.code(turn.code, language="python")
        if turn.error:
            st.error(turn.error)
        if turn.stdout.strip():
            st.text(turn.stdout)
        if turn.result_repr.strip():
            st.text(turn.result_repr)
        for fig in turn.figures:
            st.image(fig)

with st.sidebar:
    st.divider()
    st.header("Export")
    col1, col2 = st.columns(2)
    if col1.button("Save .md"):
        st.download_button(
            "Download report.md",
            to_markdown(agent),
            file_name=f"{agent.session_id}.md",
            mime="text/markdown",
        )
    if col2.button("Save .html"):
        st.download_button(
            "Download report.html",
            to_html(agent),
            file_name=f"{agent.session_id}.html",
            mime="text/html",
        )
    if st.button("Save session JSON"):
        path = agent.save_session()
        st.success(f"saved → {path}")
