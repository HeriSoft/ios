import logging
import sys

import pytest
from pydantic import ValidationError

from app_builder.core import process_manager as pm
from app_builder.core.database import MIGRATIONS, Database
from app_builder.core.redaction import RedactingFilter, redact
from app_builder.core.schemas import ChangeSet, FileChange, ProjectSpec
from app_builder.core.secret_store import SecretStore
from app_builder.services import doctor


# ---- redaction ---------------------------------------------------------------
@pytest.mark.parametrize("secret", [
    "sk-proj-abcdefghijklmnopqrstuvwxyz123456", "sk-ant-api03-abcdefghijklmnop", "AIzaSyA1234567890abcdefghijklmnopqrstuv",
    "ghp_abcdefghijklmnopqrstuvwxyz0123", "github_pat_11ABCDEFG0123456789_abcdefgh",
])
def test_redact_known_tokens(secret):
    out = redact(f"key is {secret} here")
    assert secret not in out


def test_redact_url_credentials_and_assignments():
    assert "hunter2pass" not in redact("https://user:hunter2pass@github.com/x.git")
    assert "s3cr3tvalue" not in redact("password=s3cr3tvalue")
    assert "Bearer ***" in redact("Authorization: Bearer abcdefghijklmnop123")
    assert redact("abc", ["abcdefgh"]) == "abc"
    assert "mysecretvalue" not in redact("x mysecretvalue y", ["mysecretvalue"])


def test_redacting_filter():
    rec = logging.LogRecord("t", logging.INFO, __file__, 1, "token %s", ("ghp_abcdefghijklmnopqrstuvwxyz0123",), None)
    RedactingFilter().filter(rec)
    assert "ghp_abcdef" not in rec.getMessage()


# ---- database ----------------------------------------------------------------
def test_migration_creates_all_tables(db):
    assert db.version == len(MIGRATIONS)
    names = {r[0] for r in db.query("SELECT name FROM sqlite_master WHERE type='table'")}
    for t in ("projects", "settings", "conversations", "messages", "change_sets", "checkpoints", "jobs",
              "build_artifacts", "usage_records", "model_cache", "audit_events"):
        assert t in names
    # Credentials chỉ lưu key reference — không có cột secret/api_key/token trong DB
    for t in names:
        cols = {r[1].lower() for r in db.query(f"PRAGMA table_info({t})")}
        assert not cols & {"secret", "api_key", "token", "password"}


def test_transaction_rollback(db):
    with pytest.raises(RuntimeError):
        with db.transaction() as cur:
            cur.execute("INSERT INTO settings(key, value) VALUES ('a', '1')")
            raise RuntimeError("boom")
    assert db.query_one("SELECT * FROM settings WHERE key='a'") is None


def test_migration_idempotent_on_file(tmp_path):
    p = tmp_path / "x.db"
    Database(p).close()
    d = Database(p)
    assert d.version == len(MIGRATIONS)
    d.close()


def test_newer_db_version_refused(tmp_path):
    p = tmp_path / "x.db"
    d = Database(p)
    d.conn.execute(f"PRAGMA user_version = {len(MIGRATIONS) + 5}")
    d.close()
    with pytest.raises(RuntimeError):
        Database(p)


# ---- schemas -----------------------------------------------------------------
def _spec(**kw):
    base = dict(name="App", slug="app", android_package="com.example.app", ios_bundle_id="com.example.app")
    base.update(kw)
    return ProjectSpec(**base)


def test_spec_validation():
    assert _spec().capabilities.camera is False  # quyền nhạy cảm mặc định tắt
    with pytest.raises(ValidationError):
        _spec(android_package="bad")
    with pytest.raises(ValidationError):
        _spec(platforms=[])
    with pytest.raises(ValidationError):
        _spec(name="  ")


def test_filechange_path_validated():
    with pytest.raises(ValidationError):
        FileChange(operation="create", path="../../evil.ts", content="x")
    cs = ChangeSet(id="1", changes=[FileChange(operation="update", path="app\\index.tsx", content="x")])
    assert cs.changes[0].path == "app/index.tsx"


# ---- secret store --------------------------------------------------------------
def test_memory_secret_store():
    s = SecretStore(service="AppBuilderAI-test", use_keyring=False)
    assert not s.persistent
    s.set("openai", "sk-test-value-123456")
    assert s.get("openai") == "sk-test-value-123456"
    s.delete("openai")
    assert s.get("openai") is None
    assert SecretStore.mask("sk-test-value-123456") == "sk-t••••••••3456"


# ---- process manager -------------------------------------------------------------
def test_minimal_env_strips_secrets(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-should-not-pass")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_x")
    monkeypatch.setenv("RANDOM_VAR", "x")
    env = pm.minimal_env({"EXTRA": "1"})
    assert "OPENAI_API_KEY" not in env and "GITHUB_TOKEN" not in env and "RANDOM_VAR" not in env
    assert env["EXTRA"] == "1"
    assert any(k.upper() == "PATH" for k in env)


def test_build_argv_npm_uses_node_script():
    if not pm.which("node") or not pm.node_cli_script("npm"):
        pytest.skip("Node/npm không có trên máy")
    argv = pm.build_argv(["npm", "--version"])
    assert argv[0].lower().endswith("node.exe") or argv[0].lower().endswith("node")
    assert argv[1].endswith("npm-cli.js")


@pytest.mark.skipif(sys.platform != "win32", reason="Windows .cmd")
def test_cmd_unsafe_args_rejected(tmp_path):
    bat = tmp_path / "x.cmd"
    bat.write_text("@echo ok\r\n")
    with pytest.raises(pm.UnsafeCommandError):
        pm.build_argv([str(bat), "a & calc"])
    argv = pm.build_argv([str(bat), "safe-arg"])
    assert argv[1:4] == ["/d", "/s", "/c"]
    r = pm.run([str(bat), "safe-arg"], timeout=20, env=None)
    assert r.ok and "ok" in r.stdout


def test_run_timeout_kills():
    r = pm.run([sys.executable, "-c", "import time; time.sleep(30)"], timeout=1.5)
    assert r.timed_out and not r.ok


def test_run_missing_program_and_cwd(tmp_path):
    assert pm.run(["definitely-not-a-program-xyz"], timeout=5).error
    assert pm.run([sys.executable, "-V"], cwd=tmp_path / "nope").error


def test_run_ok():
    r = pm.run([sys.executable, "-c", "print('xin chào')"], timeout=20, env=pm.minimal_env({"PYTHONIOENCODING": "utf-8"}))
    assert r.ok and "xin chào" in r.stdout


# ---- doctor ----------------------------------------------------------------------
@pytest.mark.parametrize("ver,ok", [((22, 13, 0), True), ((22, 12, 9), False), ((24, 3, 0), True), ((25, 9, 0), False),
                                    ((26, 1, 0), True), ((27, 0, 0), True), ((20, 0, 0), False)])
def test_node_engine_range(ver, ok):
    assert doctor.node_satisfies(ver, "^22.13.0 || ^24.3.0 || ^26.0.0 || >=27.0.0") is ok


def test_blocked_features_and_report():
    checks = [doctor.ToolCheck("java", "JDK", doctor.MISSING, hint="cài JDK", needed_for=["Android build"]),
              doctor.ToolCheck("git", "Git", doctor.OK, "2.4")]
    assert doctor.blocked_features(checks) == {"Android build": ["JDK"]}
    rep = doctor.format_report(checks)
    assert "BLOCKED" in rep and "cài JDK" in rep
