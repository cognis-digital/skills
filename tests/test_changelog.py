"""Tests for the changelog skill (exercises a real temporary git repo)."""
from __future__ import annotations

import json
import subprocess

import pytest
from conftest import load_skill, run_main

mod = load_skill("changelog")


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   capture_output=True, text=True)


def _has_git():
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


pytestmark = pytest.mark.skipif(not _has_git(), reason="git not available")


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "tester")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    (tmp_path / "a.txt").write_text("1", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "feat: add alpha module")
    (tmp_path / "b.txt").write_text("2", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "fix: correct beta bug")
    (tmp_path / "c.txt").write_text("3", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "random uncategorized message")
    return tmp_path


def test_categorizes_conventional_commits(repo, capsys):
    code = run_main(mod, ["--repo", str(repo), "--version", "1.2.3"])
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["version"] == "1.2.3"
    assert out["commit_count"] == 3
    assert "add alpha module" in out["sections"]["Features"]
    assert "correct beta bug" in out["sections"]["Bug Fixes"]
    assert "random uncategorized message" in out["sections"]["Other"]
    assert out["counts"]["Features"] == 1
    assert "## 1.2.3" in out["markdown"]
    assert "### Features" in out["markdown"]


def test_since_ref_limits_range(repo, capsys):
    # tag the first commit, then only later commits should appear
    _git(repo, "tag", "v0.1.0", "HEAD~2")
    run_main(mod, ["--repo", str(repo), "--since", "v0.1.0"])
    out = json.loads(capsys.readouterr().out)
    assert out["since"] == "v0.1.0"
    assert out["commit_count"] == 2


def test_not_a_git_repo_errors(tmp_path, capsys):
    code = run_main(mod, ["--repo", str(tmp_path)])
    assert code == 2
    assert "error" in json.loads(capsys.readouterr().out)
