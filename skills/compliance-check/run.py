#!/usr/bin/env python3
"""compliance-check skill: governance file + license-header verification."""
import argparse
import json
import sys
from pathlib import Path

DEFAULT_POLICY = {
    "required": ["LICENSE", "README.md", "SECURITY.md", "CODE_OF_CONDUCT.md"],
    "forbidden": [".env", "id_rsa", "id_dsa", "credentials.json", ".npmrc"],
    "require_license_header": False,
    "header_marker": "Copyright",
    "source_ext": [".py", ".js", ".ts", ".go", ".java"],
}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}


def name_matches(present_names, target):
    # case-insensitive, allow common extensions for license-like files
    t = target.lower()
    base = t.rsplit(".", 1)[0]
    for n in present_names:
        nl = n.lower()
        if nl == t or nl.rsplit(".", 1)[0] == base:
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True)
    ap.add_argument("--policy", default=None)
    a = ap.parse_args()

    root = Path(a.path)
    if not root.is_dir():
        print(json.dumps({"error": f"not a directory: {a.path}"}))
        return 2

    policy = dict(DEFAULT_POLICY)
    if a.policy:
        try:
            policy.update(json.loads(Path(a.policy).read_text(encoding="utf-8")))
        except (OSError, ValueError) as e:
            print(json.dumps({"error": f"bad policy file: {e}"}))
            return 2

    top_names = {p.name for p in root.iterdir()}
    present, missing = [], []
    for req in policy["required"]:
        (present if name_matches(top_names, req) else missing).append(req)

    forbidden_present = []
    source_files = []
    for p in root.rglob("*"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.is_file():
            if p.name in policy["forbidden"]:
                forbidden_present.append(str(p.relative_to(root)))
            if p.suffix in policy["source_ext"]:
                source_files.append(p)

    files_missing_header = []
    if policy.get("require_license_header"):
        marker = policy["header_marker"]
        for p in source_files:
            try:
                head = p.read_text(encoding="utf-8", errors="replace")[:600]
            except OSError:
                continue
            if marker not in head:
                files_missing_header.append(str(p.relative_to(root)))

    passed = not missing and not forbidden_present and not files_missing_header
    out = {
        "path": a.path,
        "passed": passed,
        "present": present,
        "missing_required": missing,
        "forbidden_present": forbidden_present,
        "files_missing_header": files_missing_header[:50],
    }
    print(json.dumps(out, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
