#!/usr/bin/env python3
"""changelog skill: build a categorized changelog from git history."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

CATEGORIES = [
    ("feat", "Features"),
    ("fix", "Bug Fixes"),
    ("perf", "Performance"),
    ("refactor", "Refactoring"),
    ("docs", "Documentation"),
    ("test", "Tests"),
    ("chore", "Chores"),
]
TYPE_RX = re.compile(r"^(\w+)(?:\([^)]*\))?!?:\s*(.+)$")


def git(args, repo):
    return subprocess.run(
        ["git", "-C", repo, *args], capture_output=True, text=True
    )


def last_tag(repo):
    r = git(["describe", "--tags", "--abbrev=0"], repo)
    return r.stdout.strip() if r.returncode == 0 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--since", default=None)
    ap.add_argument("--version", default="Unreleased")
    a = ap.parse_args()

    repo_path = Path(a.repo)
    if not repo_path.exists():
        print(json.dumps({"error": f"repo path does not exist: {a.repo}"}))
        return 2

    check = git(["rev-parse", "--is-inside-work-tree"], a.repo)
    if check.returncode != 0:
        print(json.dumps({
            "error": "not a git repository",
            "detail": check.stderr.strip(),
        }))
        return 2

    since = a.since or last_tag(a.repo)
    rng = f"{since}..HEAD" if since else "HEAD"
    log = git(["log", rng, "--pretty=format:%s", "--no-merges"], a.repo)
    if log.returncode != 0:
        print(json.dumps({"error": "git log failed", "detail": log.stderr.strip()}))
        return 1

    subjects = [s for s in log.stdout.splitlines() if s.strip()]
    buckets = {label: [] for _, label in CATEGORIES}
    buckets["Other"] = []
    cat_for = {t: label for t, label in CATEGORIES}

    for s in subjects:
        m = TYPE_RX.match(s)
        if m and m.group(1).lower() in cat_for:
            buckets[cat_for[m.group(1).lower()]].append(m.group(2).strip())
        else:
            buckets["Other"].append(s.strip())

    sections = {k: v for k, v in buckets.items() if v}
    counts = {k: len(v) for k, v in sections.items()}

    md = [f"## {a.version}", ""]
    for _, label in CATEGORIES + [("", "Other")]:
        if sections.get(label):
            md.append(f"### {label}")
            md.extend(f"- {item}" for item in sections[label])
            md.append("")
    if len(subjects) == 0:
        md.append("_No changes._")

    out = {
        "version": a.version,
        "since": since,
        "commit_count": len(subjects),
        "counts": counts,
        "sections": sections,
        "markdown": "\n".join(md).strip() + "\n",
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
