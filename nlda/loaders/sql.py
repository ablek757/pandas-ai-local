from __future__ import annotations

import pandas as pd
from sqlalchemy import create_engine


def load_sql(connection_string: str, query_or_table: str) -> pd.DataFrame:
    """Load a DataFrame from a SQL source.

    `query_or_table` may be a table name or a full SELECT statement.
    """
    engine = create_engine(connection_string)
    stripped = query_or_table.strip().lower()
    if stripped.startswith("select") or stripped.startswith("with"):
        return pd.read_sql_query(query_or_table, engine)
    return pd.read_sql_table(query_or_table, engine)
