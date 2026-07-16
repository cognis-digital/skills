# Roadmap

This roadmap describes the direction of the `cognis-skills` registry. It is a
living document; nothing here is a commitment to a date. Contributions and
comments are welcome via issues and the RFC discussion.

## Principles

- **Stdlib-first.** Skills stay dependency-free unless a `requirements` field
  explicitly declares otherwise. This keeps them trivially portable into any
  agent, CI job, or air-gapped environment.
- **JSON in / JSON out.** Every skill emits a single machine-readable object on
  stdout and reserves stderr for diagnostics. The contract never breaks.
- **Additive evolution.** New capabilities are added alongside existing ones;
  entrypoints and output shapes remain backward compatible within a major
  version.

## Near term

- **More static-analysis skills.** Extend the read-only audit family that now
  spans `secret-scan`, `repo-audit`, `compliance-check`, and `todo-scan`
  (candidates: dependency/lockfile inventory, license detection, Dockerfile
  hygiene).
- **Output formats.** Optional `--format {json,ndjson,sarif}` on the audit-style
  skills so findings can drop straight into code-scanning dashboards.
- **Registry linting in CI.** `cognis-skills validate` now runs on every push;
  next is schema-validating the frontmatter of each `SKILL.md`.

## Mid term

- **Result caching + provenance.** A thin cache keyed on inputs so agents can
  re-request a skill result cheaply, with a provenance stamp (skill version,
  timestamp) on every payload.
- **Typed result schemas.** Publish JSON Schema for each skill's output and add
  a conformance test that every skill's real output validates against its schema.
- **Parallel `run-many`.** A batch runner in the library that fans a list of
  `(skill, args)` invocations across a process pool and merges results.

## Long term

- **Cross-runtime skills.** First-class support for `bash`, `node`, and compiled
  entrypoints resolved through the same registry contract.
- **Distribution.** Publish the `cognis-skills` library + CLI to PyPI and offer a
  signed, versioned registry snapshot artifact.
- **Capability sandboxing.** Enforce the declared `permissions` (network,
  filesystem, subprocess) at run time via an opt-in restricted executor.

## How to propose a change

Open an issue describing the skill or capability, the input args, and the exact
JSON output shape. For larger directional changes, comment on the roadmap RFC
discussion so the design can be reviewed before implementation.
