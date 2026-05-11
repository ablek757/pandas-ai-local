from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_path(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    suffix = p.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(p)
    if suffix in {".tsv", ".txt"}:
        return pd.read_csv(p, sep="\t")
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(p)
    if suffix == ".parquet":
        return pd.read_parquet(p)
    if suffix == ".json":
        return pd.read_json(p)
    raise ValueError(f"Unsupported file type: {suffix}")
