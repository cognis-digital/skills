---
name: sql-explain
version: 1.0.0
description: Parse a SQL statement and explain in plain English what it does, listing tables, columns, filters, and joins touched. Use to make a query auditable.
entrypoint: run.py
runtime: python3
args:
  - name: sql
    type: string
    required: false
    description: SQL statement to explain. If omitted, read from stdin.
inputs: { stdin: true }
outputs: { format: json }
permissions: [read-only]
tags: [sql, database, explain]
---

# sql-explain

A lightweight SQL describer. Tokenizes a single statement and reports the
operation (SELECT / INSERT / UPDATE / DELETE), the tables and columns involved,
WHERE filters, JOINs, GROUP BY / ORDER BY, and a one-paragraph English summary.
It does NOT execute SQL — purely static, so it is safe on untrusted input.

## Usage

```bash
python3 run.py --sql "SELECT symbol, SUM(pnl) FROM trades WHERE strategy='ORB' GROUP BY symbol"
# or
echo "DELETE FROM positions WHERE qty = 0" | python3 run.py
```

## Output

```json
{
  "operation": "SELECT",
  "tables": ["trades"],
  "columns": ["symbol", "SUM(pnl)"],
  "filters": ["strategy = 'ORB'"],
  "group_by": ["symbol"],
  "explanation": "Reads rows from trades, ..."
}
```
