"""Tests for the summarize skill."""
from __future__ import annotations

import json

from conftest import load_skill, run_main

mod = load_skill("summarize")


def test_split_sentences_strips_markdown_and_short_fragments():
    text = "# Heading\n\nThis is a long enough first sentence about reactors. Short. "
    text += "Here is another sufficiently long second sentence about turbines."
    sents = mod.split_sentences(text)
    assert all(len(s) > 20 for s in sents)
    assert any("reactors" in s for s in sents)
    assert any("turbines" in s for s in sents)
    # short fragment excluded
    assert not any(s.strip() == "Short" for s in sents)


def test_split_sentences_removes_code_fences():
    text = (
        "A meaningful sentence that is quite long here. ```python\nx = 1\n``` "
        "Another meaningful long trailing sentence here now."
    )
    sents = mod.split_sentences(text)
    assert not any("x = 1" in s for s in sents)


def test_main_summarizes_and_ranks(tmp_path, capsys):
    doc = tmp_path / "doc.md"
    body = (
        "Nuclear power provides reliable baseload electricity for the grid. "
        "Nuclear reactors generate consistent power output around the clock. "
        "Cats are unrelated fluffy animals that nap in the sun all day long. "
        "Nuclear energy is a low-carbon source of reliable baseload power today."
    )
    doc.write_text(body, encoding="utf-8")
    code = run_main(mod, ["--file", str(doc), "--sentences", "2"])
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["summary_sentences"] == 2
    assert out["original_sentences"] == 4
    # the two nuclear-heavy sentences should outrank the cat sentence
    assert "Cats are unrelated" not in out["summary"]


def test_main_missing_file_returns_error(tmp_path, capsys):
    code = run_main(mod, ["--file", str(tmp_path / "nope.md")])
    assert code == 2
    assert "error" in json.loads(capsys.readouterr().out)
