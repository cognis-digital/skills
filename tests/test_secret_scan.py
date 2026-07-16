"""Tests for the secret-scan skill."""
from __future__ import annotations

import json
import math

from conftest import load_skill, run_main

mod = load_skill("secret-scan")


def test_shannon_bounds():
    assert mod.shannon("") == 0.0
    assert mod.shannon("aaaa") == 0.0
    # 4 distinct equiprobable symbols -> 2 bits
    assert math.isclose(mod.shannon("abcd"), 2.0, rel_tol=1e-9)


def test_redact_preserves_prefix_and_masks_tail():
    r = mod.redact("AKIAABCDEFGHIJKLMNOP")
    assert r.startswith("AKIA")
    assert set(r[4:]) == {"*"}
    short = mod.redact("abc")
    assert short[0] == "a" and set(short[1:]) == {"*"}


def test_detects_aws_key(tmp_path, capsys):
    f = tmp_path / "cfg.py"
    f.write_text('AWS = "AKIAIOSFODNN7EXAMPLE"\n', encoding="utf-8")
    code = run_main(mod, ["--path", str(tmp_path)])
    assert code == 1  # findings -> nonzero
    out = json.loads(capsys.readouterr().out)
    rules = {x["rule"] for x in out["findings"]}
    assert "aws_access_key" in rules
    # match is redacted, not the raw secret
    assert all("EXAMPLE" not in x["match"] for x in out["findings"])


def test_detects_generic_secret_assignment(tmp_path, capsys):
    f = tmp_path / "s.env"
    f.write_text("password = 'hunter2superSecret'\n", encoding="utf-8")
    code = run_main(mod, ["--path", str(tmp_path)])
    out = json.loads(capsys.readouterr().out)
    assert code == 1
    assert out["finding_count"] >= 1


def test_clean_file_no_findings(tmp_path, capsys):
    f = tmp_path / "clean.py"
    f.write_text("x = 1\nprint('hello world')\n", encoding="utf-8")
    code = run_main(mod, ["--path", str(tmp_path), "--entropy", "5.5"])
    out = json.loads(capsys.readouterr().out)
    assert code == 0
    assert out["finding_count"] == 0


def test_missing_path_errors(tmp_path, capsys):
    code = run_main(mod, ["--path", str(tmp_path / "does-not-exist")])
    assert code == 2
    assert "error" in json.loads(capsys.readouterr().out)


def test_binary_and_skip_dirs_ignored(tmp_path, capsys):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "leak.txt").write_text("AKIAIOSFODNN7EXAMPLE", encoding="utf-8")
    (tmp_path / "img.png").write_bytes(b"AKIAIOSFODNN7EXAMPLE")
    code = run_main(mod, ["--path", str(tmp_path)])
    out = json.loads(capsys.readouterr().out)
    assert code == 0
    assert out["finding_count"] == 0
