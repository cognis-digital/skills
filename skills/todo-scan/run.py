#!/usr/bin/env python3
"""todo-scan skill: find code action-markers (TODO/FIXME/HACK/...) in a tree.

Complements ``secret-scan`` and ``repo-audit`` by surfacing outstanding
engineering debt that lives inline in source. Pure stdlib, deterministic,
read-only. Emits a single JSON object on stdout:

    {
      "path": ".",
      "markers": ["TODO", "FIXME", ...],
      "finding_count": 3,
      "counts": {"TODO": 2, "FIXME": 1},
      "findings": [
        {"file": "a.py", "line": 12, "marker": "TODO", "text": "wire up cache"}
      ]
    }

Exit code is ``0`` when nothing is found and ``1`` when at least one marker is
present, so it can gate CI the same way ``secret-scan`` does.
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

DEFAULT_MARKERS = ["TODO", "FIXME", "HACK", "XXX", "BUG", "OPTIMIZE", "DEPRECATED"]

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".mypy_cache", "dist", "build"}
BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".tar",
    ".exe", ".dll", ".so", ".bin", ".ico", ".woff", ".woff2", ".ttf",
}
MAX_LINE = 2000


def build_pattern(markers):
    """Compile a case-sensitive matcher for the given markers.

    A marker only counts when it is bounded by a non-word character (or start
    of the token) so ``TODONT`` or ``autofixme`` do not match. A trailing
    ``:`` or whitespace after the marker is consumed so the captured text is
    clean.
    """
    alt = "|".join(re.escape(m) for m in markers)
    return re.compile(r"(?<![A-Za-z0-9_])(" + alt + r")(?![A-Za-z0-9_])[:\s\-]*(.*)")


def iter_files(root):
    if root.is_file():
        yield root
        return
    for p in root.rglob("*"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.is_file() and p.suffix.lower() not in BINARY_EXT:
            yield p


def scan_file(path, pattern, root):
    findings = []
    try:
        text = path.read_text(encoding="utf-8", errors="strict")
    except (UnicodeDecodeError, OSError):
        return findings
    rel = str(path.relative_to(root)) if root.is_dir() else str(path)
    for i, line in enumerate(text.splitlines(), 1):
        if len(line) > MAX_LINE:
            continue
        m = pattern.search(line)
        if m:
            findings.append(
                {
                    "file": rel,
                    "line": i,
                    "marker": m.group(1),
                    "text": m.group(2).strip()[:200],
                }
            )
    return findings


def scan(path, markers):
    """Scan ``path`` for ``markers`` and return the result payload dict."""
    root = Path(path)
    pattern = build_pattern(markers)
    findings = []
    for f in iter_files(root):
        findings.extend(scan_file(f, pattern, root))
    findings.sort(key=lambda x: (x["file"], x["line"]))
    counts = Counter(f["marker"] for f in findings)
    return {
        "path": path,
        "markers": markers,
        "finding_count": len(findings),
        "counts": {m: counts[m] for m in markers if counts[m]},
        "findings": findings,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Scan a tree for TODO/FIXME-style markers.")
    ap.add_argument("--path", required=True, help="File or directory to scan.")
    ap.add_argument(
        "--markers",
        default=",".join(DEFAULT_MARKERS),
        help="Comma-separated markers to search for.",
    )
    a = ap.parse_args(argv)

    root = Path(a.path)
    if not root.exists():
        print(json.dumps({"error": f"path not found: {a.path}"}))
        return 2

    markers = [m.strip() for m in a.markers.split(",") if m.strip()]
    if not markers:
        print(json.dumps({"error": "no markers specified"}))
        return 2

    out = scan(a.path, markers)
    print(json.dumps(out, indent=2))
    return 1 if out["finding_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
