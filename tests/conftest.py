"""Shared pytest fixtures and helpers.

Skill entrypoints live at ``skills/<name>/run.py`` and are *not* an importable
package (directory names contain hyphens). ``load_skill`` imports one by file
path under a synthetic module name so tests can call its functions directly.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parent.parent

# Make the `cognis_skills` package importable even without an editable install.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_skill(name: str) -> ModuleType:
    """Import ``skills/<name>/run.py`` as a uniquely-named module object."""
    path = ROOT / "skills" / name / "run.py"
    mod_name = f"skill_{name.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec and spec.loader, f"cannot load spec for {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


def run_main(module: ModuleType, argv_args):
    """Call ``module.main()`` with a patched ``sys.argv`` and return exit code.

    ``argv_args`` is the list of args after the program name.
    """
    saved = sys.argv
    sys.argv = ["run.py", *argv_args]
    try:
        return module.main()
    finally:
        sys.argv = saved


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


@pytest.fixture
def skill():
    """Return the ``load_skill`` helper for use inside a test."""
    return load_skill
