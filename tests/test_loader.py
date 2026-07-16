"""Tests for the reference loader (skills/loader.py)."""
from __future__ import annotations

import io
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_loader():
    import importlib.util

    spec = importlib.util.spec_from_file_location("loader_mod", ROOT / "skills" / "loader.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mod = _load_loader()


def test_load_registry_returns_skills():
    reg = mod.load_registry()
    assert "todo-scan" in reg["skills"]


def test_list_skills_prints(capsys):
    mod.list_skills()
    out = capsys.readouterr().out
    assert "web-search" in out
    assert "todo-scan" in out


def test_main_list_flag():
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = mod.main(["--list"])
    assert code == 0
    assert "secret-scan" in buf.getvalue()


def test_run_unknown_skill_returns_2():
    err = io.StringIO()
    with redirect_stderr(err):
        code = mod.run("does-not-exist", [])
    assert code == 2
    assert "unknown skill" in err.getvalue()


def test_end_to_end_subprocess():
    """The loader actually execs a skill and forwards its stdout."""
    proc = subprocess.run(
        [sys.executable, str(ROOT / "skills" / "loader.py"),
         "sql-explain", "--sql", "SELECT a FROM t"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert '"operation": "SELECT"' in proc.stdout
