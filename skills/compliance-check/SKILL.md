---
name: compliance-check
version: 1.0.0
description: Verify a repository contains required policy, license, and security governance files. Use to gate a repo before public release or external handoff.
entrypoint: run.py
runtime: python3
args:
  - name: path
    type: string
    required: true
    description: Repository root to check.
  - name: policy
    type: string
    required: false
    description: Path to a JSON policy file overriding the default required-file set.
inputs: { stdin: false }
outputs: { format: json }
permissions: [filesystem, read-only]
tags: [compliance, governance, audit]
---

# compliance-check

Checks a repository against a governance policy: required files (LICENSE,
SECURITY.md, CODE_OF_CONDUCT.md, README), forbidden files (e.g. `.env`,
`id_rsa`), and a license-header presence check on source files. Returns a pass /
fail verdict with per-rule detail.

The default policy is embedded; override it with `--policy path.json`:

```json
{
  "required": ["LICENSE", "SECURITY.md", "README.md"],
  "forbidden": [".env", "id_rsa", "credentials.json"],
  "require_license_header": true,
  "header_marker": "Copyright"
}
```

## Usage

```bash
python3 run.py --path . --policy policy.json
```

## Output

```json
{
  "path": ".",
  "passed": false,
  "present": ["README.md"],
  "missing_required": ["SECURITY.md"],
  "forbidden_present": [".env"],
  "files_missing_header": ["src/util.py"]
}
```

Exit code is non-zero on failure so it can gate CI.
