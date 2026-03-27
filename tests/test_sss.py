"""
Minimal test suite for sss — covers the parts most likely to break.
Run: pytest tests/ -v
"""
import os
import sys
import json
import importlib
import importlib.util
import tempfile
from pathlib import Path

# Load sss as a module (no .py extension — use spec_from_file_location)
SRC = Path(__file__).parent.parent / "src"
SSS_PATH = SRC / "sss"


def _load_sss(env_overrides: dict | None = None):
    """Load (or reload) the sss module, optionally with env var overrides."""
    from importlib.machinery import SourceFileLoader

    saved = {}
    if env_overrides:
        for k, v in env_overrides.items():
            saved[k] = os.environ.get(k)
            os.environ[k] = v
    try:
        loader = SourceFileLoader("sss", str(SSS_PATH))
        spec = importlib.util.spec_from_loader("sss", loader)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["sss"] = mod
        loader.exec_module(mod)
        return mod
    finally:
        for k, orig in saved.items():
            if orig is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = orig


# Load once for most tests
sss = _load_sss()


# ── 1. normalize() — German text preprocessing ──────────────────────────────

def test_normalize_umlauts():
    assert "ae" in sss.normalize("Kräuterhof")
    assert "oe" in sss.normalize("Köln")
    assert "ue" in sss.normalize("über")
    assert "ss" in sss.normalize("Straße")

def test_normalize_camelcase():
    result = sss.normalize("ErklaervideoV14")
    assert "erklaervideo" in result
    assert "14" in result

def test_normalize_empty():
    assert sss.normalize("") == ""
    assert sss.normalize(None) == ""


# ── 2. extract_text_from_message() — content block parsing ─────────────────

def test_extract_plain_string():
    msg = {"content": "Hello world"}
    assert sss.extract_text_from_message(msg) == "Hello world"

def test_extract_text_blocks():
    msg = {"content": [
        {"type": "text", "text": "First block"},
        {"type": "text", "text": "Second block"},
    ]}
    result = sss.extract_text_from_message(msg)
    assert "First block" in result
    assert "Second block" in result

def test_extract_tool_use_inputs():
    msg = {"content": [
        {"type": "tool_use", "input": {"command": "pytest tests/", "description": "Run tests"}},
    ]}
    result = sss.extract_text_from_message(msg)
    assert "pytest" in result

def test_extract_empty_content():
    assert sss.extract_text_from_message({}) == ""
    assert sss.extract_text_from_message({"content": []}) == ""


# ── 3. fingerprint_session() — milestone/deploy detection ───────────────────

def test_fingerprint_deploy_detected():
    turns = [{"text": f"running wrangler deploy now turn {i}"} for i in range(15)]
    topics, milestone, deployed = sss.fingerprint_session(turns)
    assert deployed == 1

def test_fingerprint_milestone_detected():
    turns = [{"text": f"project abgeschlossen turn {i}"} for i in range(15)]
    topics, milestone, deployed = sss.fingerprint_session(turns)
    assert milestone == 1

def test_fingerprint_short_session_no_milestone():
    # Sessions mit < 10 Turns gelten nicht als Milestone (auch wenn Pattern matcht)
    turns = [{"text": "erfolgreich deployed"} for _ in range(5)]
    topics, milestone, deployed = sss.fingerprint_session(turns)
    assert milestone == 0

def test_fingerprint_topics_extracted():
    turns = [{"text": "cloudflare worker wrangler deploy"}] * 15
    topics_json, _, _ = sss.fingerprint_session(turns)
    topics = json.loads(topics_json)
    assert "cloudflare" in topics


# ── 4. get_db() — schema migrations are idempotent ──────────────────────────

def test_db_schema_idempotent(tmp_path):
    """Running get_db() twice must not raise (migrations use try/except)."""
    custom_db = str(tmp_path / "test.db")
    mod = _load_sss({"SSS_INDEX_DB": custom_db})
    conn1 = mod.get_db()
    conn1.close()
    conn2 = mod.get_db()  # Second call: ALTER TABLE must not raise
    conn2.close()
    assert Path(custom_db).exists()


# ── 5. Env-var config ────────────────────────────────────────────────────────

def test_env_var_index_db(tmp_path):
    """SSS_INDEX_DB env var must change the actual DB path used."""
    custom_db = str(tmp_path / "custom.db")
    mod = _load_sss({"SSS_INDEX_DB": custom_db})
    assert str(mod.INDEX_DB) == custom_db

def test_env_var_embed_model():
    """SSS_EMBED_MODEL must override default."""
    mod = _load_sss({"SSS_EMBED_MODEL": "BAAI/bge-m3"})
    assert mod.EMBED_MODEL == "BAAI/bge-m3"

def test_env_var_sessions_dir(tmp_path):
    """SSS_SESSIONS_DIR must override default SESSIONS_BASE."""
    mod = _load_sss({"SSS_SESSIONS_DIR": str(tmp_path)})
    assert mod.SESSIONS_BASE == tmp_path


# ── 6. analyze() — analytics engine ─────────────────────────────────────────

def _make_test_db(tmp_path):
    """Create a minimal populated DB for analytics tests."""
    import sqlite3
    db_path = str(tmp_path / "test-analyze.db")
    mod = _load_sss({"SSS_INDEX_DB": db_path})
    conn = mod.get_db()
    # Insert two sessions with topics and metadata
    conn.execute("""
        INSERT OR IGNORE INTO sessions_meta
            (session_id, project, first_ts, last_ts, turn_count, active_minutes,
             milestone_detected, deploy_detected, topics)
        VALUES
            ('aaaa', 'project-alpha', '2026-01-10T10:00:00', '2026-01-10T11:00:00',
             20, 60, 1, 0, '["seo", "cloudflare"]'),
            ('bbbb', 'project-alpha', '2026-01-17T10:00:00', '2026-01-17T11:30:00',
             15, 90, 0, 1, '["briefadler", "cloudflare"]'),
            ('cccc', 'project-beta',  '2026-01-24T09:00:00', '2026-01-24T09:30:00',
             8,  30, 0, 0, '["seo"]')
    """)
    conn.execute("""
        INSERT INTO turns_fts (session_id, project, role, timestamp, text)
        VALUES
            ('aaaa', 'project-alpha', 'user',      '2026-01-10T10:00:00', 'deployment error traceback in wrangler'),
            ('bbbb', 'project-alpha', 'assistant', '2026-01-17T10:00:00', 'same issue again with cloudflare'),
            ('cccc', 'project-beta',  'user',      '2026-01-24T09:00:00', 'seo analysis completed successfully')
    """)
    conn.commit()
    conn.close()
    return mod, db_path


def test_analyze_topics_runs(tmp_path, capsys):
    mod, db_path = _make_test_db(tmp_path)
    mod.analyze("topics")
    out = capsys.readouterr().out
    assert "cloudflare" in out
    assert "seo" in out


def test_analyze_projects_runs(tmp_path, capsys):
    mod, db_path = _make_test_db(tmp_path)
    mod.analyze("projects")
    out = capsys.readouterr().out
    assert "project-alpha" in out


def test_analyze_errors_runs(tmp_path, capsys):
    mod, db_path = _make_test_db(tmp_path)
    mod.analyze("errors")
    out = capsys.readouterr().out
    assert "error" in out.lower() or "turns" in out.lower()


def test_analyze_friction_runs(tmp_path, capsys):
    mod, db_path = _make_test_db(tmp_path)
    mod.analyze("friction")
    out = capsys.readouterr().out
    assert "friction" in out.lower() or "pain" in out.lower() or "turns" in out.lower()


def test_analyze_timeline_runs(tmp_path, capsys):
    mod, db_path = _make_test_db(tmp_path)
    mod.analyze("timeline")
    out = capsys.readouterr().out
    assert "sessions" in out.lower()


def test_analyze_keyword_runs(tmp_path, capsys):
    mod, db_path = _make_test_db(tmp_path)
    mod.analyze("wrangler")
    out = capsys.readouterr().out
    assert "wrangler" in out.lower()


def test_analyze_keyword_no_results(tmp_path, capsys):
    mod, db_path = _make_test_db(tmp_path)
    mod.analyze("xyznotexistentterm12345")
    out = capsys.readouterr().out
    assert "No results" in out or "no results" in out.lower()
