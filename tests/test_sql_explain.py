"""Tests for the sql-explain skill."""
from __future__ import annotations

import json

from conftest import load_skill, run_main

mod = load_skill("sql-explain")


def test_clean_strips_comments_and_semicolons():
    sql = "SELECT 1 -- a comment\n/* block */ FROM t;"
    cleaned = mod.clean(sql)
    assert "--" not in cleaned
    assert "/*" not in cleaned
    assert not cleaned.endswith(";")
    assert "FROM t" in cleaned


def test_split_list_respects_parentheses():
    assert mod.split_list("a, b, c") == ["a", "b", "c"]
    # comma inside function call must not split
    assert mod.split_list("COALESCE(a, b), c") == ["COALESCE(a, b)", "c"]


def test_select_with_join_where_group(capsys):
    sql = (
        "SELECT o.id, COUNT(*) FROM orders o "
        "JOIN users u ON u.id = o.user_id "
        "WHERE o.total > 100 AND u.active = 1 GROUP BY o.id ORDER BY o.id LIMIT 10"
    )
    code = run_main(mod, ["--sql", sql])
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["operation"] == "SELECT"
    assert "orders" in out["tables"]
    assert out["joins"] == ["users"]
    assert out["group_by"] == ["o.id"]
    assert len(out["filters"]) == 2
    assert out["explanation"].startswith("Reads")


def test_insert_statement(capsys):
    code = run_main(mod, ["--sql", "INSERT INTO logs (level, msg) VALUES ('x', 'y')"])
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["operation"] == "INSERT"
    assert out["tables"] == ["logs"]
    assert out["columns"] == ["level", "msg"]
    assert out["explanation"].startswith("Inserts rows into logs")


def test_update_statement(capsys):
    code = run_main(mod, ["--sql", "UPDATE users SET active = 0 WHERE id = 5"])
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["operation"] == "UPDATE"
    assert out["tables"] == ["users"]
    assert out["columns"] == ["active"]
    assert out["filters"] == ["id = 5"]


def test_delete_statement(capsys):
    code = run_main(mod, ["--sql", "DELETE FROM sessions WHERE expired = 1"])
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["operation"] == "DELETE"
    assert out["tables"] == ["sessions"]


def test_empty_statement_errors(capsys):
    code = run_main(mod, ["--sql", "   "])
    assert code == 2
    assert "error" in json.loads(capsys.readouterr().out)
