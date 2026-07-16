"""Structural integrity tests for registry.json and the skill tree."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
REG = json.loads((ROOT / "registry.json").read_text(encoding="utf-8"))
SKILLS = REG["skills"]


def test_registry_schema_header():
    assert REG["schema"].startswith("cognis-skills/registry@")
    assert isinstance(SKILLS, dict) and SKILLS


@pytest.mark.parametrize("name", sorted(SKILLS))
def test_key_matches_meta_name(name):
    assert SKILLS[name]["name"] == name


@pytest.mark.parametrize("name", sorted(SKILLS))
def test_entrypoint_exists(name):
    meta = SKILLS[name]
    entry = ROOT / meta["path"] / meta["entrypoint"]
    assert entry.is_file(), f"missing entrypoint for {name}: {entry}"


@pytest.mark.parametrize("name", sorted(SKILLS))
def test_skill_md_exists(name):
    meta = SKILLS[name]
    assert (ROOT / meta["path"] / "SKILL.md").is_file()


@pytest.mark.parametrize("name", sorted(SKILLS))
def test_required_meta_fields(name):
    meta = SKILLS[name]
    for field in ("name", "version", "description", "path", "entrypoint", "runtime"):
        assert meta.get(field), f"{name} missing field {field}"
    assert isinstance(meta.get("permissions", []), list)
    assert isinstance(meta.get("tags", []), list)


def test_every_skill_dir_is_registered():
    """No orphan skill directory (has SKILL.md but absent from registry)."""
    skills_dir = ROOT / "skills"
    for child in skills_dir.iterdir():
        if child.is_dir() and (child / "SKILL.md").is_file():
            assert child.name in SKILLS, f"unregistered skill dir: {child.name}"


def test_todo_scan_registered():
    assert "todo-scan" in SKILLS
    assert SKILLS["todo-scan"]["path"] == "skills/todo-scan"
