from fastapi.testclient import TestClient

from main import app


def test_context_graph_declares_non_authoritative_phase2_boundary():
    response = TestClient(app).get("/authority")
    assert response.status_code == 200
    body = response.json()
    assert body["authoritative_service"] == "unison-context"
    assert body["durable_personal_memory"] is False
    assert body["relationship_access_grants"] is False
    assert "ephemeral_environmental_state" in body["allowed_data"]
