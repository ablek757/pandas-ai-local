import pytest

import pandas as pd

from nlda.sandbox import run_code, UnsafeCodeError, _static_check


def _df():
    return pd.DataFrame({"a": [1, 2, 3, 4], "b": [10, 20, 30, 40]})


def test_basic_aggregation():
    res = run_code("result = df['a'].sum()", {"df": _df()})
    assert res.ok
    assert res.result == 10


def test_assigns_result_dataframe():
    res = run_code(
        "result = df.assign(c=df.a + df.b)",
        {"df": _df()},
    )
    assert res.ok
    assert "c" in res.result.columns


def test_blocks_import():
    with pytest.raises(UnsafeCodeError):
        _static_check("import os")


def test_blocks_dunder():
    with pytest.raises(UnsafeCodeError):
        _static_check("x = (1).__class__")


def test_blocks_open_builtin():
    res = run_code("result = open('x')", {"df": _df()})
    assert not res.ok
    assert "blocked" in res.error.lower() or "name" in res.error.lower()


def test_runtime_error_is_captured():
    res = run_code("result = df['missing'].sum()", {"df": _df()})
    assert not res.ok
    assert "KeyError" in res.error or "missing" in res.error


def test_chart_capture():
    code = (
        "fig, ax = plt.subplots()\n"
        "df.plot(ax=ax)\n"
        "result = 'chart drawn'\n"
    )
    res = run_code(code, {"df": _df()})
    assert res.ok
    assert len(res.figures) == 1
    assert res.figures[0][:8].startswith(b"\x89PNG")


def test_timeout():
    code = "x=0\nwhile True:\n    x+=1"
    res = run_code(code, {"df": _df()}, timeout=0.5)
    assert not res.ok
    assert "timeout" in res.error.lower()
