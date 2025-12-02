---
name: repo-audit
version: 1.0.0
description: Static health audit of a code repository - size, language mix, large files, and missing metadata. Use before onboarding or releasing a repo.
entrypoint: run.py
runtime: python3
args:
  - name: path
    type: string
    required: true
    description: Path to the repository root.
  - name: large-mb
    type: float
    required: false
    description: Threshold in MB for flagging large files (default 5).
inputs: { stdin: false }
outputs: { format: json }
permissions: [filesystem, read-only]
tags: [code, audit, quality]
---

# repo-audit

Walks a repository and reports a structural health snapshot: total files, total
bytes, language breakdown by extension, the largest files, and which common
metadata files (README, LICENSE, .gitignore, tests) are missing.

Skips `.git`, `node_modules`, `__pycache__`, and `.venv` to stay fast.

## Usage

```bash
python3 run.py --path . --large-mb 2
```

## Output

```json
{
  "path": ".",
  "file_count": 142,
  "total_bytes": 884213,
  "languages": {".py": 61, ".md": 12, ".json": 4},
  "large_files": [{"file": "data/dump.csv", "bytes": 3145728}],
  "missing_meta": ["LICENSE"],
  "score": 0.83
}
```
