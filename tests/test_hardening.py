"""Hardening tests: edge cases and bad-input paths for cognis-skills."""
import json
import subprocess
import sys
from pathlib import Path

PYTHON = sys.executable
ROOT = Path(__file__).resolve().parent.parent


def run(script, *args, stdin=None):
    """Run a skill script and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        [PYTHON, str(script), *args],
        capture_output=True,
        text=True,
        input=stdin,
    )
    return result.returncode, result.stdout, result.stderr


# ---------------------------------------------------------------------------
# loader.py
# ---------------------------------------------------------------------------

class TestLoader:
    LOADER = ROOT / "skills" / "loader.py"

    def test_unknown_skill_exits_2(self):
        rc, out, err = run(self.LOADER, "nonexistent-skill-xyz")
        assert rc == 2
        assert "unknown skill" in err

    def test_list_runs_ok(self):
        rc, out, err = run(self.LOADER, "--list")
        assert rc == 0
        assert "web-search" in out

    def test_bad_registry_exits_2(self, tmp_path):
        """Loader must exit 2 cleanly when registry.json is malformed."""
        # Build a fake repo tree with a bad registry.json
        fake_root = tmp_path / "fakerepo"
        fake_root.mkdir()
        fake_skills = fake_root / "skills"
        fake_skills.mkdir()
        (fake_root / "registry.json").write_text(
            "{ not valid json }", encoding="utf-8"
        )
        # Copy loader.py into fake_skills so ROOT resolves to fake_root
        import shutil
        shutil.copy(str(self.LOADER), str(fake_skills / "loader.py"))

        rc, out, err = run(fake_skills / "loader.py", "web-search")
        assert rc == 2
        assert "malformed" in err.lower() or "registry" in err.lower()


# ---------------------------------------------------------------------------
# web-search/run.py
# ---------------------------------------------------------------------------

class TestWebSearch:
    SCRIPT = ROOT / "skills" / "web-search" / "run.py"

    def test_empty_query_exits_2(self):
        rc, out, err = run(self.SCRIPT, "--query", "   ")
        assert rc == 2
        assert "empty" in err.lower()

    def test_max_zero_exits_2(self):
        rc, out, err = run(self.SCRIPT, "--query", "test", "--max", "0")
        assert rc == 2
        assert "positive" in err.lower() or "--max" in err.lower()

    def test_max_negative_exits_2(self):
        rc, out, err = run(self.SCRIPT, "--query", "test", "--max", "-5")
        assert rc == 2


# ---------------------------------------------------------------------------
# secret-scan/run.py
# ---------------------------------------------------------------------------

class TestSecretScan:
    SCRIPT = ROOT / "skills" / "secret-scan" / "run.py"

    def test_missing_path_exits_2(self):
        rc, out, err = run(self.SCRIPT, "--path", "/no/such/path/xyz")
        assert rc == 2
        payload = json.loads(out)
        assert "error" in payload

    def test_bad_entropy_exits_2(self):
        rc, out, err = run(self.SCRIPT, "--path", ".", "--entropy", "-1")
        assert rc == 2
        assert "entropy" in err.lower()

    def test_entropy_too_large_exits_2(self):
        rc, out, err = run(self.SCRIPT, "--path", ".", "--entropy", "9")
        assert rc == 2

    def test_empty_dir_no_findings(self, tmp_path):
        rc, out, err = run(self.SCRIPT, "--path", str(tmp_path))
        assert rc == 0
        payload = json.loads(out)
        assert payload["finding_count"] == 0
        assert payload["findings"] == []


# ---------------------------------------------------------------------------
# sql-explain/run.py
# ---------------------------------------------------------------------------

class TestSqlExplain:
    SCRIPT = ROOT / "skills" / "sql-explain" / "run.py"

    def test_empty_sql_exits_2(self):
        rc, out, err = run(self.SCRIPT, stdin="")
        assert rc == 2
        payload = json.loads(out)
        assert "error" in payload

    def test_whitespace_only_sql_exits_2(self):
        rc, out, err = run(self.SCRIPT, "--sql", "   ;  ")
        assert rc == 2

    def test_valid_select(self):
        rc, out, err = run(
            self.SCRIPT, "--sql", "SELECT id, name FROM users WHERE id = 1"
        )
        assert rc == 0
        payload = json.loads(out)
        assert payload["operation"] == "SELECT"
        assert "users" in payload["tables"]


# ---------------------------------------------------------------------------
# summarize/run.py
# ---------------------------------------------------------------------------

class TestSummarize:
    SCRIPT = ROOT / "skills" / "summarize" / "run.py"

    def test_missing_file_exits_2(self):
        rc, out, err = run(self.SCRIPT, "--file", "/no/such/file.md")
        assert rc == 2
        payload = json.loads(out)
        assert "error" in payload

    def test_sentences_zero_exits_2(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text(
            "Hello world. This is a test sentence. And another one.",
            encoding="utf-8",
        )
        rc, out, err = run(self.SCRIPT, "--file", str(f), "--sentences", "0")
        assert rc == 2
        assert "positive" in err.lower()

    def test_empty_file_returns_error(self, tmp_path):
        f = tmp_path / "empty.md"
        f.write_text("", encoding="utf-8")
        rc, out, err = run(self.SCRIPT, "--file", str(f))
        assert rc in (1, 2)
        payload = json.loads(out)
        assert "error" in payload


# ---------------------------------------------------------------------------
# osint-lookup/run.py
# ---------------------------------------------------------------------------

class TestOsintLookup:
    SCRIPT = ROOT / "skills" / "osint-lookup" / "run.py"

    def test_empty_host_exits_2(self):
        rc, out, err = run(self.SCRIPT, "--host", "   ")
        assert rc == 2
        assert "empty" in err.lower()

    def test_host_with_slash_exits_2(self):
        rc, out, err = run(self.SCRIPT, "--host", "http://example.com/path")
        assert rc == 2
        assert "hostname" in err.lower() or "valid" in err.lower()


# ---------------------------------------------------------------------------
# compliance-check/run.py
# ---------------------------------------------------------------------------

class TestComplianceCheck:
    SCRIPT = ROOT / "skills" / "compliance-check" / "run.py"

    def test_missing_path_exits_2(self):
        rc, out, err = run(self.SCRIPT, "--path", "/no/such/dir/xyz")
        assert rc == 2
        payload = json.loads(out)
        assert "error" in payload

    def test_bad_policy_json_exits_2(self, tmp_path):
        bad_policy = tmp_path / "policy.json"
        bad_policy.write_text("not json at all", encoding="utf-8")
        # Create a minimal dir to pass the directory check
        target = tmp_path / "repo"
        target.mkdir()
        rc, out, err = run(
            self.SCRIPT, "--path", str(target), "--policy", str(bad_policy)
        )
        assert rc == 2
        payload = json.loads(out)
        assert "error" in payload

    def test_empty_dir_missing_required(self, tmp_path):
        rc, out, err = run(self.SCRIPT, "--path", str(tmp_path))
        assert rc == 1  # fails because required files are absent
        payload = json.loads(out)
        assert payload["passed"] is False
        assert len(payload["missing_required"]) > 0


# ---------------------------------------------------------------------------
# changelog/run.py
# ---------------------------------------------------------------------------

class TestChangelog:
    SCRIPT = ROOT / "skills" / "changelog" / "run.py"

    def test_nonexistent_repo_exits_2(self):
        rc, out, err = run(self.SCRIPT, "--repo", "/no/such/repo/xyz")
        assert rc == 2
        payload = json.loads(out)
        assert "error" in payload

    def test_non_git_dir_exits_2(self, tmp_path):
        rc, out, err = run(self.SCRIPT, "--repo", str(tmp_path))
        assert rc == 2
        payload = json.loads(out)
        assert "error" in payload

    def test_valid_repo_runs(self):
        # ROOT is a valid git repo (it was cloned from GitHub)
        rc, out, err = run(self.SCRIPT, "--repo", str(ROOT))
        assert rc == 0
        payload = json.loads(out)
        assert "commit_count" in payload
        assert "markdown" in payload


# ---------------------------------------------------------------------------
# repo-audit/run.py
# ---------------------------------------------------------------------------

class TestRepoAudit:
    SCRIPT = ROOT / "skills" / "repo-audit" / "run.py"

    def test_missing_path_exits_2(self):
        rc, out, err = run(self.SCRIPT, "--path", "/no/such/dir/xyz")
        assert rc == 2
        payload = json.loads(out)
        assert "error" in payload

    def test_empty_dir_runs(self, tmp_path):
        rc, out, err = run(self.SCRIPT, "--path", str(tmp_path))
        assert rc == 0
        payload = json.loads(out)
        assert payload["file_count"] == 0
        assert isinstance(payload["score"], float)
