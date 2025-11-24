import importlib
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)


def make_client(tmp_db):
    os.environ["CONTEXT_GRAPH_DB_PATH"] = tmp_db
    os.environ["DURABILITY_TTL_DAYS"] = "0"
    os.environ["DURABILITY_PII_AFTER_DAYS"] = "0"
    import main as main

    importlib.reload(main)
    return TestClient(main.app)


def test_durability_status_and_metrics():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "db.sqlite")
        client = make_client(db_path)

        res = client.get("/durability/status")
        assert res.status_code == 200
        body = res.json()
        assert "wal" in body and "ttl" in body and "pii_scrubbing" in body

        metrics = client.get("/metrics").json()
        assert "wal_checkpoints" in metrics


def test_ttl_and_pii_triggers_delete_and_scrub():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "db.sqlite")
        client = make_client(db_path)

        # Insert an expired record directly
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.execute(
            """
            INSERT INTO event_traces (
                trace_id, person_id, session_id, event_type, timestamp,
                event_data, context_snapshot, created_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "expired-trace",
                "user-123",
                "session-abc",
                "test",
                datetime.utcnow().isoformat(),
                "{}",
                "{}",
                (datetime.utcnow() - timedelta(days=2)).isoformat(),
                (datetime.utcnow() - timedelta(days=1)).isoformat(),
            ),
        )
        conn.commit()
        conn.close()

        ttl_res = client.post("/durability/run_ttl")
        assert ttl_res.status_code == 200
        assert ttl_res.json()["deleted"] >= 1

        pii_res = client.post("/durability/run_pii")
        assert pii_res.status_code == 200
        # No rows remain so scrubbed may be 0, but endpoint should respond
    assert "metrics" in pii_res.json()


def test_capabilities_round_trip():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "db.sqlite")
        client = make_client(db_path)

        manifest = {"modalities": {"displays": [{"id": "d1"}]}}
        res = client.post("/capabilities", json=manifest)
        assert res.status_code == 200
        res2 = client.get("/capabilities")
        assert res2.status_code == 200
        body = res2.json()
        assert body["manifest"]["modalities"]["displays"][0]["id"] == "d1"
        # Ensure persisted in SQLite
        conn = sqlite3.connect(db_path, check_same_thread=False)
        cur = conn.cursor()
        cur.execute("SELECT manifest FROM capabilities WHERE id = 1")
        row = cur.fetchone()
        conn.close()
        assert row is not None
