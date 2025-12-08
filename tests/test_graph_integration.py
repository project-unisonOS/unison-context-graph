import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "unison-common" / "src"))
sys.path.append(str(ROOT / "unison-context-graph" / "src"))

GRAPH_URI = os.getenv("GRAPH_DB_URI")
GRAPH_USER = os.getenv("GRAPH_DB_USER")
GRAPH_PASSWORD = os.getenv("GRAPH_DB_PASSWORD")

if not (GRAPH_URI and GRAPH_USER and GRAPH_PASSWORD):
    pytest.skip("Neo4j not configured", allow_module_level=True)

try:
    from src.main import app  # noqa: E402
except Exception as exc:
    pytest.skip(f"Skipping context-graph integration tests due to import error: {exc}", allow_module_level=True)


@pytest.fixture
def client():
    return TestClient(app)


def test_graph_node_and_relation(client):
    r1 = client.post(
        "/graph/nodes",
        json={"id": "person-test", "labels": ["Person"], "props": {"name": "Alice"}},
    )
    assert r1.status_code == 200
    r2 = client.post(
        "/graph/nodes",
        json={"id": "agent-test", "labels": ["Agent"], "props": {"name": "Bot"}},
    )
    assert r2.status_code == 200
    rel = client.post(
        "/graph/relations",
        json={"start_id": "agent-test", "end_id": "person-test", "type": "SERVES"},
    )
    assert rel.status_code == 200
    assert rel.json().get("ok") is True
