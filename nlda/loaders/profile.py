"""Lightweight DataFrame profiling — fed to the LLM as analysis context."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def profile_dataframe(df: pd.DataFrame, sample_rows: int = 3) -> dict[str, Any]:
    cols: list[dict[str, Any]] = []
    for name in df.columns:
        s = df[name]
        info: dict[str, Any] = {
            "name": str(name),
            "dtype": str(s.dtype),
            "nulls": int(s.isna().sum()),
            "unique": int(s.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(s):
            non_null = s.dropna()
            if len(non_null):
                info["min"] = _to_py(non_null.min())
                info["max"] = _to_py(non_null.max())
                info["mean"] = _to_py(round(float(non_null.mean()), 4))
        elif pd.api.types.is_datetime64_any_dtype(s):
            non_null = s.dropna()
            if len(non_null):
                info["min"] = str(non_null.min())
                info["max"] = str(non_null.max())
        else:
            top = s.dropna().astype(str).value_counts().head(3)
            info["top_values"] = [
                {"value": str(idx), "count": int(cnt)} for idx, cnt in top.items()
            ]
        cols.append(info)

    return {
        "shape": {"rows": int(df.shape[0]), "cols": int(df.shape[1])},
        "columns": cols,
        "head": df.head(sample_rows).to_dict(orient="records"),
    }


def _to_py(v: Any) -> Any:
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    return v


def render_profile_text(profile: dict[str, Any]) -> str:
    """Compact text rendering of a profile, intended for LLM context."""
    lines = [f"shape: {profile['shape']['rows']} rows x {profile['shape']['cols']} cols"]
    lines.append("columns:")
    for c in profile["columns"]:
        bits = [f"  - {c['name']} ({c['dtype']}, nulls={c['nulls']}, unique={c['unique']})"]
        for k in ("min", "max", "mean"):
            if k in c:
                bits.append(f"{k}={c[k]}")
        if "top_values" in c:
            tv = ", ".join(f"{t['value']}({t['count']})" for t in c["top_values"])
            bits.append(f"top=[{tv}]")
        lines.append(" ".join(bits))
    lines.append("sample rows:")
    for row in profile["head"]:
        lines.append(f"  {row}")
    return "\n".join(lines)
