---
name: changelog
version: 1.0.0
description: Generate a categorized changelog section from git commit history since a ref or tag. Use when cutting a release or summarizing recent work.
entrypoint: run.py
runtime: python3
args:
  - name: since
    type: string
    required: false
    description: Git ref/tag to start from (default - last tag, else all history).
  - name: repo
    type: string
    required: false
    description: Path to the git repo (default current directory).
  - name: version
    type: string
    required: false
    description: Version label for the changelog header (default Unreleased).
inputs: { stdin: false }
outputs: { format: json }
permissions: [subprocess, read-only]
tags: [git, release, docs]
---

# changelog

Reads `git log` since a ref and buckets commits into Conventional-Commit
categories (feat, fix, docs, refactor, perf, test, chore, other). Emits both a
structured JSON object and a ready-to-paste Markdown `markdown` field.

## Usage

```bash
python3 run.py --repo . --since v1.2.0 --version 1.3.0
```

## Output

```json
{
  "version": "1.3.0",
  "since": "v1.2.0",
  "counts": {"feat": 3, "fix": 5},
  "sections": {"Features": ["add foo"], "Bug Fixes": ["handle null"]},
  "markdown": "## 1.3.0\n\n### Features\n- add foo\n..."
}
```
