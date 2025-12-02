---
name: secret-scan
version: 1.0.0
description: Scan files for leaked credentials using known-pattern regexes and Shannon-entropy heuristics. Use before committing or publishing any repository.
entrypoint: run.py
runtime: python3
args:
  - name: path
    type: string
    required: true
    description: File or directory to scan.
  - name: entropy
    type: float
    required: false
    description: Minimum base64 entropy bits to flag a high-entropy string (default 4.0).
inputs: { stdin: false }
outputs: { format: json }
permissions: [filesystem, read-only]
tags: [security, secrets, audit]
---

# secret-scan

Scans text files for leaked secrets. Two detectors:

1. **Pattern match** — AWS keys, Google API keys, Slack tokens, GitHub PATs,
   private-key headers, generic `password=`/`secret=` assignments.
2. **Entropy heuristic** — long base64/hex tokens whose Shannon entropy exceeds
   the threshold, which often indicates a key or token.

Findings include file, line number, a redacted match, and rule id. Binary files
and `.git`/`node_modules` are skipped.

## Usage

```bash
python3 run.py --path ./src --entropy 4.2
```

## Output

```json
{
  "path": "./src",
  "findings": [
    {"file": "src/cfg.py", "line": 12, "rule": "aws_access_key", "match": "AKIA****************"}
  ],
  "finding_count": 1
}
```

Exit code is non-zero when findings exist, so it can gate a pre-commit hook.
