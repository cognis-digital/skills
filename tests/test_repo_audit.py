"""Tests for the repo-audit skill."""
from __future__ import annotations

import json

from conftest import load_skill, run_main

mod = load_skill("repo-audit")


def _write(base, rel, content=b"x"):
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        content = content.encode()
    p.write_bytes(content)
    return p


def test_full_repo_high_score(tmp_path, capsys):
    _write(tmp_path, "README.md", "# hi")
    _write(tmp_path, "LICENSE", "MIT")
    _write(tmp_path, ".gitignore", "*.pyc")
    _write(tmp_path, "src/app.py", "print(1)\n")
    _write(tmp_path, "tests/test_app.py", "def test_x():\n    assert True\n")
    code = run_main(mod, ["--path", str(tmp_path)])
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["missing_meta"] == []
    assert out["has_tests"] is True
    assert out["score"] == 1.0
    assert ".py" in out["languages"]


def test_missing_meta_penalizes_score(tmp_path, capsys):
    workdir = tmp_path / "proj"
    _write(workdir, "main.py", "print(1)\n")
    run_main(mod, ["--path", str(workdir)])
    out = json.loads(capsys.readouterr().out)
    assert "README.md" in out["missing_meta"]
    assert "LICENSE" in out["missing_meta"]
    assert out["score"] < 1.0
    # each missing meta file costs 0.15
    assert out["score"] <= 1.0 - 0.15 * len(out["missing_meta"]) + 1e-9


def test_large_file_reported(tmp_path, capsys):
    _write(tmp_path, "README.md", "# hi")
    _write(tmp_path, "big.bin", b"0" * (2 * 1024 * 1024))
    run_main(mod, ["--path", str(tmp_path), "--large-mb", "1"])
    out = json.loads(capsys.readouterr().out)
    assert any(f["file"] == "big.bin" for f in out["large_files"])
    assert out["large_files"][0]["bytes"] >= 2 * 1024 * 1024


def test_skip_dirs_excluded_from_count(tmp_path, capsys):
    _write(tmp_path, "app.py", "x=1")
    _write(tmp_path, "node_modules/pkg/index.js", "y=2")
    run_main(mod, ["--path", str(tmp_path)])
    out = json.loads(capsys.readouterr().out)
    assert ".js" not in out["languages"]


def test_not_a_directory_errors(tmp_path, capsys):
    f = tmp_path / "file.txt"
    f.write_text("x", encoding="utf-8")
    code = run_main(mod, ["--path", str(f)])
    assert code == 2
    assert "error" in json.loads(capsys.readouterr().out)
