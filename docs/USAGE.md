# Usage

Three ways to use the registry, from lowest to highest level.

## 1. Run a skill directly

Skills are standalone scripts. Nothing to install:

```bash
python3 skills/web-search/run.py --query "critical minerals export controls"
python3 skills/secret-scan/run.py --path ./src --entropy 4.2
python3 skills/todo-scan/run.py --path . --markers "TODO,FIXME,REVIEW"
python3 skills/sql-explain/run.py --sql "SELECT id FROM orders WHERE total > 100"
python3 skills/repo-audit/run.py --path . > audit.json
```

Each prints one JSON object to stdout. Exit codes:

| Code | Meaning |
|------|---------|
| `0`  | success (audit skills: nothing found) |
| `1`  | soft failure / findings present (e.g. secret-scan, todo-scan) |
| `2`  | usage/input error (bad path, empty statement, ...) |

## 2. The reference loader

`skills/loader.py` resolves a name from the registry and execs it:

```bash
python3 skills/loader.py --list
python3 skills/loader.py web-search --query "iran oil sanctions"
python3 skills/loader.py secret-scan --path .
```

## 3. The `cognis-skills` library and CLI

Install the typed library once and get a console command plus a Python API:

```bash
pip install -e .          # from a checkout
```

### CLI

```bash
cognis-skills list                 # human-readable table
cognis-skills list --json          # machine-readable
cognis-skills run sql-explain --sql "SELECT 1 FROM t"
cognis-skills validate             # check registry <-> filesystem <-> manifests
cognis-skills validate --json
```

`validate` exits non-zero if any *error*-level inconsistency is found, so it can
gate CI.

### Python API

```python
from cognis_skills import list_skills, run_skill, validate

# Discover
for s in list_skills():
    print(s.name, s.version, s.permissions)

# Invoke and consume parsed JSON
result = run_skill("secret-scan", ["--path", "."])
print(result.ok, result.returncode)
for finding in result.data["findings"]:
    print(finding["file"], finding["line"], finding["rule"])

# Guard the registry in your own tooling
issues = validate()
assert not [i for i in issues if i.severity == "error"]
```

`run_skill` returns a `SkillResult(skill, returncode, stdout, stderr, data)`,
where `data` is the parsed JSON (or `None` if the skill emitted none). Unknown
skills raise `RegistryError`; process-level failures are reported through the
result object rather than by raising.

## Composing skills

Because every skill speaks JSON, they pipe together with ordinary tools:

```bash
# Audit a repo, then pretty-print the missing metadata
python3 skills/repo-audit/run.py --path . | python -c \
  "import sys,json; print(json.load(sys.stdin)['missing_meta'])"
```

## Notes

- Set `PYTHONUTF8=1` on Windows to guarantee UTF-8 decoding of inputs.
- Network skills (`web-search`, `osint-lookup`) require outbound access and no
  API keys.
