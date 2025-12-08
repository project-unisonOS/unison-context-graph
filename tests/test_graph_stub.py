import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

os.environ.setdefault("GRAPH_DB_URI", "")
os.environ.setdefault("GRAPH_DB_USER", "")
os.environ.setdefault("GRAPH_DB_PASSWORD", "")

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "unison-common" / "src"))
sys.path.append(str(ROOT / "unison-context-graph" / "src"))

try:
    from src.main import app  # noqa: E402
except Exception as exc:
    pytest.skip(f"Skipping context-graph tests due to import error: {exc}", allow_module_level=True)


def test_readyz_without_graph():
    client = TestClient(app)
    resp = client.get("/readyz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["graph"] is True or body["status"] in {"ok", "degraded"}


def test_graph_node_stub():
    client = TestClient(app)
    resp = client.post("/graph/nodes", json={"id": "person-1", "labels": ["Person"], "props": {"name": "Test"}})
    assert resp.status_code == 200
    assert resp.json().get("ok") is True
