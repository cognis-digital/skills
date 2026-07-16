"""Registry access: locate ``registry.json`` and resolve skills to entrypoints."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class RegistryError(RuntimeError):
    """Raised when the registry cannot be located, parsed, or resolved."""


@dataclass(frozen=True)
class Skill:
    """A single registry entry, resolved against a repository root."""

    name: str
    version: str
    description: str
    path: str
    entrypoint: str
    runtime: str
    permissions: list[str]
    tags: list[str]

    @classmethod
    def from_meta(cls, name: str, meta: dict) -> Skill:
        return cls(
            name=meta.get("name", name),
            version=meta.get("version", ""),
            description=meta.get("description", ""),
            path=meta.get("path", f"skills/{name}"),
            entrypoint=meta.get("entrypoint", "run.py"),
            runtime=meta.get("runtime", "python3"),
            permissions=list(meta.get("permissions", [])),
            tags=list(meta.get("tags", [])),
        )


def find_root(start: Path | None = None) -> Path:
    """Return the repository root that contains ``registry.json``.

    Searches ``start`` (default: this file's location) and its parents. Raises
    :class:`RegistryError` if no ``registry.json`` is found.
    """
    here = (start or Path(__file__)).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "registry.json").is_file():
            return candidate
    raise RegistryError("registry.json not found in any parent directory")


def load_registry(root: Path | None = None) -> dict:
    """Load and return the parsed ``registry.json`` document."""
    root = root or find_root()
    reg_path = root / "registry.json"
    try:
        return json.loads(reg_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:  # pragma: no cover - filesystem/JSON errors
        raise RegistryError(f"cannot read registry: {exc}") from exc


def list_skills(root: Path | None = None) -> list[Skill]:
    """Return every registered skill as a :class:`Skill`, sorted by name."""
    reg = load_registry(root)
    skills = reg.get("skills", {})
    return [Skill.from_meta(name, meta) for name, meta in sorted(skills.items())]


def get_skill(name: str, root: Path | None = None) -> Skill:
    """Return a single skill by name, or raise :class:`RegistryError`."""
    reg = load_registry(root)
    skills = reg.get("skills", {})
    if name not in skills:
        available = ", ".join(sorted(skills)) or "(none)"
        raise RegistryError(f"unknown skill '{name}'. Available: {available}")
    return Skill.from_meta(name, skills[name])


def resolve_entrypoint(skill: Skill, root: Path | None = None) -> Path:
    """Return the absolute path to a skill's entrypoint script."""
    root = root or find_root()
    return (root / skill.path / skill.entrypoint).resolve()
