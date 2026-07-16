"""Tests for the cognis_skills library and CLI."""
from __future__ import annotations

import json

import pytest

import cognis_skills
from cognis_skills import (
    RegistryError,
    list_skills,
    load_registry,
    run_skill,
    validate,
)
from cognis_skills.cli import main as cli_main
from cognis_skills.validate import parse_frontmatter


def test_load_registry_and_list():
    reg = load_registry()
    assert "skills" in reg
    names = {s.name for s in list_skills()}
    assert {"web-search", "secret-scan", "todo-scan"} <= names


def test_skill_dataclass_fields():
    skills = {s.name: s for s in list_skills()}
    ss = skills["secret-scan"]
    assert ss.entrypoint == "run.py"
    assert ss.runtime == "python3"
    assert "read-only" in ss.permissions


def test_run_skill_parses_json():
    # todo-scan on the tests dir will find markers in this very file's fixtures? use a temp
    res = run_skill("sql-explain", ["--sql", "SELECT a FROM t"])
    assert res.ok
    assert res.data is not None
    assert res.data["operation"] == "SELECT"


def test_run_skill_nonzero_still_parses(tmp_path):
    f = tmp_path / "x.py"
    f.write_text("# TODO: something\n", encoding="utf-8")
    res = run_skill("todo-scan", ["--path", str(tmp_path)])
    assert res.returncode == 1  # markers found
    assert res.data["finding_count"] == 1


def test_run_skill_unknown_raises():
    with pytest.raises(RegistryError):
        run_skill("no-such-skill")


def test_validate_is_clean_on_this_repo():
    issues = validate()
    errors = [i for i in issues if i.severity == "error"]
    assert errors == [], f"unexpected registry errors: {errors}"


def test_parse_frontmatter_scalars():
    md = "---\nname: demo\nversion: 2.0.0\nentrypoint: run.py\nargs:\n  - name: x\n---\nbody"
    fm = parse_frontmatter(md)
    assert fm["name"] == "demo"
    assert fm["version"] == "2.0.0"
    assert fm["entrypoint"] == "run.py"
    assert "args" not in fm  # list value skipped


def test_parse_frontmatter_none_without_fence():
    assert parse_frontmatter("no frontmatter here") == {}


def test_cli_list_json(capsys):
    rc = cli_main(["list", "--json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert any(s["name"] == "todo-scan" for s in data)


def test_cli_validate_ok(capsys):
    rc = cli_main(["validate"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "OK" in out


def test_cli_validate_json(capsys):
    rc = cli_main(["validate", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert data["ok"] is True


def test_cli_run_passthrough(capsys):
    rc = cli_main(["run", "sql-explain", "--sql", "SELECT 1 FROM t"])
    out = capsys.readouterr().out
    assert rc == 0
    assert json.loads(out)["operation"] == "SELECT"


def test_cli_run_unknown_skill():
    rc = cli_main(["run", "nope"])
    assert rc == 2


def test_version_exposed():
    assert isinstance(cognis_skills.__version__, str)
