#!/usr/bin/env python3
"""Reference loader for the cognis-skills registry.

Resolves a skill by name from registry.json and execs its entrypoint, passing
remaining CLI args straight through. Captures the skill's JSON stdout and
re-emits it, so the loader itself is composable.

Usage:
    python3 skills/loader.py <skill-name> [-- skill args...]
    python3 skills/loader.py --list

Examples:
    python3 skills/loader.py web-search --query "critical minerals"
    python3 skills/loader.py secret-scan --path .
    python3 skills/loader.py --list
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "registry.json"


def load_registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def list_skills():
    reg = load_registry()
    for name, meta in reg["skills"].items():
        print(f"{name:18s} {meta['description']}")


def run(name, passthrough):
    reg = load_registry()
    skills = reg["skills"]
    if name not in skills:
        sys.stderr.write(
            f"unknown skill '{name}'. Available: {', '.join(sorted(skills))}\n"
        )
        return 2
    meta = skills[name]
    entry = ROOT / meta["path"] / meta["entrypoint"]
    if not entry.is_file():
        sys.stderr.write(f"entrypoint missing: {entry}\n")
        return 2
    runtime = meta.get("runtime", "python3")
    interp = sys.executable if runtime in ("python3", "python") else runtime
    cmd = [interp, str(entry), *passthrough]
    proc = subprocess.run(cmd)
    return proc.returncode


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        sys.stderr.write(__doc__)
        return 0
    if argv[0] == "--list":
        list_skills()
        return 0
    name = argv[0]
    passthrough = argv[1:]
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]
    return run(name, passthrough)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
