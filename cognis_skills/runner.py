"""Run a skill entrypoint as a subprocess and capture its JSON result."""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .registry import RegistryError, Skill, find_root, get_skill, resolve_entrypoint


@dataclass
class SkillResult:
    """The outcome of running a skill.

    ``data`` is the parsed JSON object emitted on stdout (``None`` if the skill
    produced no valid JSON). ``stdout``/``stderr`` are the raw streams and
    ``returncode`` is the process exit status.
    """

    skill: str
    returncode: int
    stdout: str
    stderr: str
    data: dict | None = field(default=None)

    @property
    def ok(self) -> bool:
        """True when the process exited 0."""
        return self.returncode == 0


def _interpreter(runtime: str) -> str:
    return sys.executable if runtime in ("python3", "python") else runtime


def run_skill(
    name: str,
    args: list[str] | None = None,
    root: Path | None = None,
    timeout: float | None = None,
) -> SkillResult:
    """Resolve ``name`` from the registry, exec its entrypoint, and parse stdout.

    ``args`` are passed through verbatim as CLI flags (e.g. ``["--path", "."]``).
    Raises :class:`RegistryError` if the skill is unknown or its entrypoint is
    missing; process failures are reported via the returned
    :class:`SkillResult`, not exceptions.
    """
    root = root or find_root()
    skill: Skill = get_skill(name, root)
    entry = resolve_entrypoint(skill, root)
    if not entry.is_file():
        raise RegistryError(f"entrypoint missing for '{name}': {entry}")

    cmd = [_interpreter(skill.runtime), str(entry), *(args or [])]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout
    )
    data: dict | None = None
    if proc.stdout.strip():
        try:
            data = json.loads(proc.stdout)
        except ValueError:
            data = None
    return SkillResult(
        skill=name,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        data=data,
    )
