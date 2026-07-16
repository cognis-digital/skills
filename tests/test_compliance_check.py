"""Tests for the compliance-check skill."""
from __future__ import annotations

import json

from conftest import load_skill, run_main

mod = load_skill("compliance-check")


def test_name_matches_case_and_extension_insensitive():
    names = {"license.md", "README.md"}
    assert mod.name_matches(names, "LICENSE")
    assert mod.name_matches(names, "README.md")
    assert not mod.name_matches(names, "SECURITY.md")


def test_passing_repo(tmp_path, capsys):
    for f in ("LICENSE", "README.md", "SECURITY.md", "CODE_OF_CONDUCT.md"):
        (tmp_path / f).write_text("x", encoding="utf-8")
    code = run_main(mod, ["--path", str(tmp_path)])
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["passed"] is True
    assert out["missing_required"] == []


def test_missing_required_fails(tmp_path, capsys):
    (tmp_path / "README.md").write_text("x", encoding="utf-8")
    code = run_main(mod, ["--path", str(tmp_path)])
    assert code == 1
    out = json.loads(capsys.readouterr().out)
    assert out["passed"] is False
    assert "LICENSE" in out["missing_required"]
    assert "SECURITY.md" in out["missing_required"]


def test_forbidden_file_fails(tmp_path, capsys):
    for f in ("LICENSE", "README.md", "SECURITY.md", "CODE_OF_CONDUCT.md"):
        (tmp_path / f).write_text("x", encoding="utf-8")
    (tmp_path / ".env").write_text("SECRET=1", encoding="utf-8")
    code = run_main(mod, ["--path", str(tmp_path)])
    out = json.loads(capsys.readouterr().out)
    assert code == 1
    assert ".env" in out["forbidden_present"]


def test_custom_policy_license_header(tmp_path, capsys):
    for f in ("LICENSE", "README.md", "SECURITY.md", "CODE_OF_CONDUCT.md"):
        (tmp_path / f).write_text("x", encoding="utf-8")
    good = tmp_path / "good.py"
    good.write_text("# Copyright 2026 Cognis\nx = 1\n", encoding="utf-8")
    bad = tmp_path / "bad.py"
    bad.write_text("x = 1\n", encoding="utf-8")
    policy = tmp_path / "policy.json"
    policy.write_text(json.dumps({"require_license_header": True}), encoding="utf-8")
    code = run_main(mod, ["--path", str(tmp_path), "--policy", str(policy)])
    out = json.loads(capsys.readouterr().out)
    assert code == 1
    assert "bad.py" in out["files_missing_header"]
    assert "good.py" not in out["files_missing_header"]


def test_not_a_directory_errors(tmp_path, capsys):
    code = run_main(mod, ["--path", str(tmp_path / "nope")])
    assert code == 2
    assert "error" in json.loads(capsys.readouterr().out)
