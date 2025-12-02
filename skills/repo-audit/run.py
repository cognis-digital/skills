#!/usr/bin/env python3
"""repo-audit skill: structural health snapshot of a repository."""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".mypy_cache"}
META_FILES = {
    "readme": ("README.md", "README.rst", "README.txt"),
    "license": ("LICENSE", "LICENSE.md", "LICENSE.txt"),
    "gitignore": (".gitignore",),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True)
    ap.add_argument("--large-mb", type=float, default=5.0)
    a = ap.parse_args()

    root = Path(a.path)
    if not root.is_dir():
        print(json.dumps({"error": f"not a directory: {a.path}"}))
        return 2

    large_threshold = int(a.large_mb * 1024 * 1024)
    langs = Counter()
    file_count = 0
    total_bytes = 0
    large_files = []
    has_tests = False
    present_names = set()

    for p in root.rglob("*"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.is_file():
            file_count += 1
            try:
                size = p.stat().st_size
            except OSError:
                size = 0
            total_bytes += size
            ext = p.suffix.lower() or "<none>"
            langs[ext] += 1
            present_names.add(p.name)
            if "test" in p.name.lower() or "test" in str(p.parent).lower():
                has_tests = True
            if size >= large_threshold:
                large_files.append(
                    {"file": str(p.relative_to(root)), "bytes": size}
                )

    missing = []
    for key, names in META_FILES.items():
        if not any(n in present_names for n in names):
            missing.append(names[0])
    if not has_tests:
        missing.append("tests/")

    # crude health score: 1.0 minus penalties
    score = 1.0
    score -= 0.15 * len(missing)
    score -= 0.05 * min(len(large_files), 4)
    score = round(max(0.0, score), 2)

    large_files.sort(key=lambda x: x["bytes"], reverse=True)
    out = {
        "path": a.path,
        "file_count": file_count,
        "total_bytes": total_bytes,
        "languages": dict(langs.most_common()),
        "large_files": large_files[:10],
        "missing_meta": missing,
        "has_tests": has_tests,
        "score": score,
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
