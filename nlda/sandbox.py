"""Restricted-namespace executor for LLM-generated pandas / matplotlib code.

This is **defence in depth**, not a security boundary. A sufficiently motivated
attacker who controls the prompt can usually escape. The point is to catch
obvious mistakes by the LLM (writing files, shelling out, etc.) and give the
user a clear error.
"""

from __future__ import annotations

import ast
import io
import threading
from dataclasses import dataclass, field
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BANNED_NAMES = {
    "os", "sys", "subprocess", "socket", "shutil", "pathlib",
    "open", "eval", "exec", "compile", "__import__", "globals", "locals",
    "input", "exit", "quit", "vars",
}

BANNED_ATTR_PREFIX = "__"


class UnsafeCodeError(Exception):
    pass


class ExecutionTimeout(Exception):
    pass


@dataclass
class ExecResult:
    stdout: str = ""
    result: Any = None
    figures: list[bytes] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


def _static_check(code: str) -> None:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise UnsafeCodeError(f"Syntax error: {e}") from e

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise UnsafeCodeError("`import` is not allowed in generated code.")
        if isinstance(node, ast.Attribute) and node.attr.startswith(BANNED_ATTR_PREFIX):
            raise UnsafeCodeError(f"Access to dunder attribute {node.attr!r} blocked.")
        if isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            raise UnsafeCodeError(f"Use of name {node.id!r} blocked.")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in BANNED_NAMES:
                raise UnsafeCodeError(f"Call to {node.func.id!r} blocked.")


def _capture_figures() -> list[bytes]:
    figs: list[bytes] = []
    for num in plt.get_fignums():
        fig = plt.figure(num)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
        figs.append(buf.getvalue())
    plt.close("all")
    return figs


def run_code(
    code: str,
    dataframes: dict[str, pd.DataFrame],
    timeout: float = 20.0,
) -> ExecResult:
    """Execute `code` against `dataframes` and capture stdout / figures / `result`."""
    try:
        _static_check(code)
    except UnsafeCodeError as e:
        return ExecResult(error=f"UnsafeCodeError: {e}")

    namespace: dict[str, Any] = {
        "pd": pd,
        "np": np,
        "plt": plt,
        "result": None,
        **dataframes,
    }
    namespace["__builtins__"] = _safe_builtins()

    buf = io.StringIO()
    out = ExecResult()
    done = threading.Event()
    err_box: dict[str, BaseException] = {}

    def target() -> None:
        import contextlib
        try:
            with contextlib.redirect_stdout(buf):
                exec(compile(code, "<generated>", "exec"), namespace)
        except BaseException as e:  # noqa: BLE001 - we record and surface
            err_box["e"] = e
        finally:
            done.set()

    t = threading.Thread(target=target, daemon=True)
    t.start()
    finished = done.wait(timeout=timeout)
    if not finished:
        out.error = f"Execution exceeded {timeout}s timeout."
        return out

    out.stdout = buf.getvalue()
    out.figures = _capture_figures()
    if "e" in err_box:
        out.error = f"{type(err_box['e']).__name__}: {err_box['e']}"
        return out
    out.result = namespace.get("result")
    return out


def _safe_builtins() -> dict[str, Any]:
    import builtins as B

    allowed = {
        "abs", "all", "any", "bool", "dict", "enumerate", "filter", "float",
        "int", "len", "list", "map", "max", "min", "print", "range", "reversed",
        "round", "set", "slice", "sorted", "str", "sum", "tuple", "zip",
        "isinstance", "type",
    }
    return {name: getattr(B, name) for name in allowed if hasattr(B, name)}
