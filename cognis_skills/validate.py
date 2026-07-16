"""Integrity checks that the registry, filesystem, and manifests agree.

This powers ``cognis-skills validate`` and is safe to run in CI: it never
mutates anything and returns a list of :class:`ValidationIssue`. A registry
this small is easy to let drift (a renamed directory, a bumped version in one
place but not the other), so an automated cross-check is genuinely useful.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .registry import Skill, find_root, list_skills

_SCALAR_RE = re.compile(r"^([A-Za-z0-9_]+):\s*(.+?)\s*$")


@dataclass(frozen=True)
class ValidationIssue:
    """A single problem found during validation."""

    severity: str  # "error" or "warning"
    skill: str
    message: str

    def __str__(self) -> str:
        return f"[{self.severity}] {self.skill}: {self.message}"


def parse_frontmatter(md_text: str) -> dict[str, str]:
    """Extract the top-level scalar keys from a SKILL.md YAML frontmatter block.

    Deliberately minimal (no third-party YAML dependency): it reads the leading
    ``---`` fenced block and returns simple ``key: value`` scalars, ignoring
    nested/list structures. Sufficient to cross-check ``name``, ``version``,
    ``entrypoint``, and ``runtime``.
    """
    lines = md_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        # only capture unindented scalars; skip list items and nested maps
        if line[:1] in (" ", "\t", "-"):
            continue
        m = _SCALAR_RE.match(line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def _check_skill(skill: Skill, root: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    sdir = root / skill.path
    if not sdir.is_dir():
        issues.append(ValidationIssue("error", skill.name, f"path missing: {skill.path}"))
        return issues

    entry = sdir / skill.entrypoint
    if not entry.is_file():
        issues.append(
            ValidationIssue("error", skill.name, f"entrypoint missing: {skill.entrypoint}")
        )

    manifest = sdir / "SKILL.md"
    if not manifest.is_file():
        issues.append(ValidationIssue("error", skill.name, "SKILL.md missing"))
        return issues

    fm = parse_frontmatter(manifest.read_text(encoding="utf-8"))
    if not fm:
        issues.append(ValidationIssue("warning", skill.name, "SKILL.md has no frontmatter"))
        return issues

    if fm.get("name") != skill.name:
        issues.append(
            ValidationIssue(
                "error",
                skill.name,
                f"SKILL.md name '{fm.get('name')}' != registry name '{skill.name}'",
            )
        )
    if fm.get("version") and fm["version"] != skill.version:
        issues.append(
            ValidationIssue(
                "error",
                skill.name,
                f"version mismatch: SKILL.md {fm['version']} != registry {skill.version}",
            )
        )
    if fm.get("entrypoint") and fm["entrypoint"] != skill.entrypoint:
        issues.append(
            ValidationIssue(
                "error",
                skill.name,
                f"entrypoint mismatch: SKILL.md {fm['entrypoint']} != registry {skill.entrypoint}",
            )
        )
    return issues


def _check_orphans(registered: dict[str, Skill], root: Path) -> list[ValidationIssue]:
    """Flag skill directories on disk that are absent from the registry."""
    issues: list[ValidationIssue] = []
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return issues
    for child in sorted(skills_dir.iterdir()):
        if not child.is_dir():
            continue
        if not (child / "SKILL.md").is_file():
            continue
        if child.name not in registered:
            issues.append(
                ValidationIssue(
                    "error",
                    child.name,
                    "skill directory has SKILL.md but is not in registry.json",
                )
            )
    return issues


def validate(root: Path | None = None) -> list[ValidationIssue]:
    """Return every consistency issue across registry, filesystem, and manifests.

    An empty list means the registry is fully consistent.
    """
    root = root or find_root()
    skills = list_skills(root)
    registered = {s.name: s for s in skills}
    issues: list[ValidationIssue] = []
    for skill in skills:
        issues.extend(_check_skill(skill, root))
    issues.extend(_check_orphans(registered, root))
    return issues
