"""Tests for the new todo-scan skill."""
from __future__ import annotations

import json

from conftest import load_skill, run_main

mod = load_skill("todo-scan")


def test_build_pattern_is_word_bounded():
    pat = mod.build_pattern(["TODO", "FIXME"])
    assert pat.search("# TODO: fix this")
    assert pat.search("x = 1  # FIXME later")
    # embedded in a larger word must not match
    assert not pat.search("TODONT do this")
    assert not pat.search("autofixme()")


def test_scan_reports_marker_line_and_text(tmp_path):
    f = tmp_path / "a.py"
    f.write_text(
        "def g():\n"
        "    # TODO: wire up cache\n"
        "    return 1  # FIXME: handle None\n",
        encoding="utf-8",
    )
    out = mod.scan(str(tmp_path), mod.DEFAULT_MARKERS)
    assert out["finding_count"] == 2
    by_marker = {x["marker"]: x for x in out["findings"]}
    assert by_marker["TODO"]["line"] == 2
    assert by_marker["TODO"]["text"] == "wire up cache"
    assert by_marker["FIXME"]["line"] == 3
    assert out["counts"] == {"TODO": 1, "FIXME": 1}


def test_findings_sorted_by_file_then_line(tmp_path):
    (tmp_path / "z.py").write_text("# TODO one\n", encoding="utf-8")
    (tmp_path / "a.py").write_text("# TODO two\n# TODO three\n", encoding="utf-8")
    out = mod.scan(str(tmp_path), ["TODO"])
    order = [(f["file"], f["line"]) for f in out["findings"]]
    assert order == sorted(order)
    assert order[0][0].endswith("a.py")


def test_custom_markers_only(tmp_path, capsys):
    f = tmp_path / "n.py"
    f.write_text("# TODO x\n# REVIEW y\n", encoding="utf-8")
    code = run_main(mod, ["--path", str(tmp_path), "--markers", "REVIEW"])
    assert code == 1
    out = json.loads(capsys.readouterr().out)
    assert out["finding_count"] == 1
    assert out["findings"][0]["marker"] == "REVIEW"


def test_clean_tree_exit_zero(tmp_path, capsys):
    (tmp_path / "clean.py").write_text("x = 1\n", encoding="utf-8")
    code = run_main(mod, ["--path", str(tmp_path)])
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["finding_count"] == 0
    assert out["counts"] == {}


def test_skip_dirs_and_binaries(tmp_path, capsys):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "x.py").write_text("# TODO ignored\n", encoding="utf-8")
    (tmp_path / "img.png").write_bytes(b"# TODO ignored binary")
    (tmp_path / "real.py").write_text("# TODO counted\n", encoding="utf-8")
    run_main(mod, ["--path", str(tmp_path)])
    out = json.loads(capsys.readouterr().out)
    assert out["finding_count"] == 1
    assert out["findings"][0]["file"].endswith("real.py")


def test_single_file_scan(tmp_path, capsys):
    f = tmp_path / "solo.py"
    f.write_text("# HACK: temporary\n", encoding="utf-8")
    code = run_main(mod, ["--path", str(f)])
    assert code == 1
    out = json.loads(capsys.readouterr().out)
    assert out["findings"][0]["marker"] == "HACK"


def test_missing_path_errors(tmp_path, capsys):
    code = run_main(mod, ["--path", str(tmp_path / "nope")])
    assert code == 2
    assert "error" in json.loads(capsys.readouterr().out)
