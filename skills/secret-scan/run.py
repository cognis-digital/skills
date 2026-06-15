#!/usr/bin/env python3
"""secret-scan skill: regex + entropy credential scanner."""
import argparse
import json
import math
import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}
BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip",
    ".gz", ".exe", ".dll", ".so", ".bin",
}

PATTERNS = {
    "aws_access_key": re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
    "google_api_key": re.compile(r"\b(AIza[0-9A-Za-z\-_]{35})\b"),
    "slack_token": re.compile(r"\b(xox[baprs]-[0-9A-Za-z\-]{10,})\b"),
    "github_pat": re.compile(r"\b(gh[pousr]_[0-9A-Za-z]{36,})\b"),
    "private_key": re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
    ),
    "generic_secret": re.compile(
        r"(?i)(?:password|passwd|secret|api[_-]?key|token)\s*[:=]\s*['\"]?([^\s'\"]{8,})"
    ),
}

HIGH_ENTROPY = re.compile(r"[A-Za-z0-9+/=_\-]{24,}")


def shannon(s):
    if not s:
        return 0.0
    freq = {c: s.count(c) for c in set(s)}
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in freq.values())


def redact(s):
    if len(s) <= 6:
        return s[0] + "*" * (len(s) - 1)
    return s[:4] + "*" * (len(s) - 4)


def scan_file(p, entropy_min):
    findings = []
    try:
        lines = p.read_text(encoding="utf-8", errors="strict").splitlines()
    except (UnicodeDecodeError, OSError):
        return findings
    for i, line in enumerate(lines, 1):
        if len(line) > 4000:
            continue
        for rule, rx in PATTERNS.items():
            m = rx.search(line)
            if m:
                hit = m.group(1) if m.groups() else m.group(0)
                findings.append({
                    "file": str(p), "line": i,
                    "rule": rule, "match": redact(hit),
                })
        for tok in HIGH_ENTROPY.findall(line):
            if shannon(tok) >= entropy_min and not any(
                f["line"] == i for f in findings
            ):
                findings.append({
                    "file": str(p), "line": i,
                    "rule": "high_entropy", "match": redact(tok),
                })
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True)
    ap.add_argument("--entropy", type=float, default=4.0)
    a = ap.parse_args()

    if a.entropy < 0 or a.entropy > 8:
        sys.stderr.write(
            "error: --entropy must be between 0 and 8 "
            "(Shannon entropy of a random 64-char string is ~6)\n"
        )
        return 2

    root = Path(a.path)
    targets = []
    if root.is_file():
        targets = [root]
    elif root.is_dir():
        for p in root.rglob("*"):
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if p.is_file() and p.suffix.lower() not in BINARY_EXT:
                targets.append(p)
    else:
        print(json.dumps({"error": f"path not found: {a.path}"}))
        return 2

    findings = []
    for p in targets:
        findings.extend(scan_file(p, a.entropy))

    out = {"path": a.path, "finding_count": len(findings), "findings": findings}
    print(json.dumps(out, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
