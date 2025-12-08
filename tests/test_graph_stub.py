import os
from fastapi.testclient import TestClient

os.environ.setdefault("GRAPH_DB_URI", "")
os.environ.setdefault("GRAPH_DB_USER", "")
os.environ.setdefault("GRAPH_DB_PASSWORD", "")

from src.main import app  # noqa: E402


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
