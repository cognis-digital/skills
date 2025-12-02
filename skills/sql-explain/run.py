#!/usr/bin/env python3
"""sql-explain skill: static plain-English describer for a single SQL statement."""
import argparse
import json
import re
import sys


def clean(sql):
    sql = re.sub(r"--[^\n]*", " ", sql)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return re.sub(r"\s+", " ", sql).strip().rstrip(";")


def grab(pattern, sql, flags=re.I):
    m = re.search(pattern, sql, flags)
    return m.group(1).strip() if m else None


def split_list(s):
    return [x.strip() for x in re.split(r",(?![^()]*\))", s) if x.strip()] if s else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sql", default=None)
    a = ap.parse_args()
    sql = a.sql if a.sql is not None else sys.stdin.read()
    sql = clean(sql)
    if not sql:
        print(json.dumps({"error": "empty statement"}))
        return 2

    op = sql.split(" ", 1)[0].upper()
    res = {"operation": op, "tables": [], "columns": [], "filters": []}

    if op == "SELECT":
        cols = grab(r"SELECT\s+(.*?)\s+FROM\s", sql + " ")
        res["columns"] = split_list(cols)
        frm = grab(r"FROM\s+(.*?)(?:\s+WHERE|\s+GROUP|\s+ORDER|\s+LIMIT|$)", sql)
        if frm:
            res["tables"] = [t.split()[0] for t in re.split(r"\bJOIN\b", frm, flags=re.I)]
        joins = re.findall(r"JOIN\s+(\S+)", sql, re.I)
        if joins:
            res["joins"] = joins
        gb = grab(r"GROUP BY\s+(.*?)(?:\s+ORDER|\s+LIMIT|$)", sql)
        if gb:
            res["group_by"] = split_list(gb)
        ob = grab(r"ORDER BY\s+(.*?)(?:\s+LIMIT|$)", sql)
        if ob:
            res["order_by"] = split_list(ob)
    elif op == "INSERT":
        res["tables"] = [grab(r"INTO\s+(\S+)", sql) or "?"]
        cols = grab(r"INTO\s+\S+\s*\((.*?)\)", sql)
        res["columns"] = split_list(cols)
    elif op == "UPDATE":
        res["tables"] = [grab(r"UPDATE\s+(\S+)", sql) or "?"]
        sets = grab(r"SET\s+(.*?)(?:\s+WHERE|$)", sql)
        res["columns"] = [s.split("=")[0].strip() for s in split_list(sets)]
    elif op == "DELETE":
        res["tables"] = [grab(r"FROM\s+(\S+)", sql) or "?"]

    where = grab(r"WHERE\s+(.*?)(?:\s+GROUP|\s+ORDER|\s+LIMIT|$)", sql)
    if where:
        res["filters"] = [c.strip() for c in re.split(r"\b(?:AND|OR)\b", where, flags=re.I)]

    verb = {
        "SELECT": "Reads",
        "INSERT": "Inserts rows into",
        "UPDATE": "Updates rows in",
        "DELETE": "Deletes rows from",
    }.get(op, "Operates on")
    tbls = ", ".join(res["tables"]) or "an unspecified table"
    expl = f"{verb} {tbls}"
    if res["columns"] and op in ("SELECT", "INSERT", "UPDATE"):
        expl += f", touching columns: {', '.join(res['columns'])}"
    if res["filters"]:
        expl += f". Restricted to rows where {' and '.join(res['filters'])}"
    if res.get("group_by"):
        expl += f". Aggregated by {', '.join(res['group_by'])}"
    expl += "."
    res["explanation"] = expl

    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
