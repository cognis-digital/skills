"""cognis_skills — a small, dependency-free library over the skill registry.

The repository ships a set of standalone skill scripts under ``skills/`` indexed
by ``registry.json``. This package wraps that registry with a typed, importable
API and a console entry point (``cognis-skills``) so agents and CI can:

* discover skills programmatically (:func:`load_registry`, :func:`list_skills`),
* run a skill and parse its JSON result (:func:`run_skill`),
* validate that the registry, the filesystem, and each ``SKILL.md`` manifest
  agree (:func:`validate`).

Nothing here changes the behavior of the existing scripts or the reference
``skills/loader.py`` — it is a strictly additive convenience layer built on the
same registry contract.
"""
from __future__ import annotations

from .registry import (
    RegistryError,
    Skill,
    find_root,
    list_skills,
    load_registry,
    resolve_entrypoint,
)
from .runner import SkillResult, run_skill
from .validate import ValidationIssue, validate

__all__ = [
    "RegistryError",
    "Skill",
    "SkillResult",
    "ValidationIssue",
    "find_root",
    "list_skills",
    "load_registry",
    "resolve_entrypoint",
    "run_skill",
    "validate",
]

__version__ = "1.1.0"
