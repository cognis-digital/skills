---
name: todo-scan
version: 1.0.0
description: Scan a codebase for TODO/FIXME/HACK-style action markers and report file, line, and text. Use to inventory inline engineering debt before a release or review.
entrypoint: run.py
runtime: python3
args:
  - name: path
    type: string
    required: true
    description: File or directory to scan.
  - name: markers
    type: string
    required: false
    description: Comma-separated markers to search for (default TODO,FIXME,HACK,XXX,BUG,OPTIMIZE,DEPRECATED).
inputs: { stdin: false }
outputs: { format: json }
permissions: [filesystem, read-only]
tags: [code, quality, audit, debt]
---

# todo-scan

Inventories inline engineering debt by scanning text files for action markers
such as `TODO`, `FIXME`, `HACK`, `XXX`, `BUG`, `OPTIMIZE`, and `DEPRECATED`.
It complements `secret-scan` (credentials) and `repo-audit` (structure) as the
third read-only static-analysis skill in the registry.

Matching is **word-bounded** and case-sensitive, so `TODONT` or `autofixme`
never match. Binary files and `.git`/`node_modules`/build directories are
skipped. Findings are sorted by file then line for stable, diff-friendly output.

## Usage

```bash
# Default marker set
python3 run.py --path ./src

# Custom markers
python3 run.py --path . --markers "TODO,FIXME,REVIEW"
```

## Output

```json
{
  "path": "./src",
  "markers": ["TODO", "FIXME", "HACK", "XXX", "BUG", "OPTIMIZE", "DEPRECATED"],
  "finding_count": 2,
  "counts": {"TODO": 1, "FIXME": 1},
  "findings": [
    {"file": "src/cache.py", "line": 12, "marker": "TODO", "text": "wire up cache eviction"},
    {"file": "src/io.py", "line": 88, "marker": "FIXME", "text": "handle short reads"}
  ]
}
```

Exit code is `0` when no markers are found and `1` when at least one is present,
so it can gate CI or a pre-commit hook just like `secret-scan`.
