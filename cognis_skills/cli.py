"""``cognis-skills`` console entry point.

Subcommands:

* ``list``               — list registered skills (``--json`` for machine output).
* ``run <name> [args…]`` — run a skill; args after ``--`` pass through.
* ``validate``           — cross-check registry, filesystem, and manifests.

This is additive: the historical ``python skills/loader.py`` interface keeps
working unchanged.
"""
from __future__ import annotations

import argparse
import json
import sys

from .registry import RegistryError, list_skills
from .runner import run_skill
from .validate import validate


def _cmd_list(args: argparse.Namespace) -> int:
    skills = list_skills()
    if args.json:
        payload = [
            {
                "name": s.name,
                "version": s.version,
                "description": s.description,
                "permissions": s.permissions,
                "tags": s.tags,
            }
            for s in skills
        ]
        print(json.dumps(payload, indent=2))
    else:
        for s in skills:
            print(f"{s.name:18s} {s.description}")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    passthrough = list(args.args)
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]
    try:
        result = run_skill(args.name, passthrough)
    except RegistryError as exc:
        sys.stderr.write(f"{exc}\n")
        return 2
    if result.stdout:
        sys.stdout.write(result.stdout)
        if not result.stdout.endswith("\n"):
            sys.stdout.write("\n")
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode


def _cmd_validate(args: argparse.Namespace) -> int:
    issues = validate()
    errors = [i for i in issues if i.severity == "error"]
    if args.json:
        print(
            json.dumps(
                {
                    "ok": not errors,
                    "issue_count": len(issues),
                    "issues": [
                        {"severity": i.severity, "skill": i.skill, "message": i.message}
                        for i in issues
                    ],
                },
                indent=2,
            )
        )
    else:
        if not issues:
            print("registry OK: all skills consistent")
        else:
            for i in issues:
                print(str(i))
    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cognis-skills", description="Cognis skill registry CLI.")
    sub = p.add_subparsers(dest="command", required=True)

    pl = sub.add_parser("list", help="List registered skills.")
    pl.add_argument("--json", action="store_true", help="Emit JSON.")
    pl.set_defaults(func=_cmd_list)

    pr = sub.add_parser("run", help="Run a skill by name.")
    pr.add_argument("name", help="Skill name.")
    pr.add_argument("args", nargs=argparse.REMAINDER, help="Args passed to the skill.")
    pr.set_defaults(func=_cmd_run)

    pv = sub.add_parser("validate", help="Check registry/filesystem/manifest consistency.")
    pv.add_argument("--json", action="store_true", help="Emit JSON.")
    pv.set_defaults(func=_cmd_validate)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
