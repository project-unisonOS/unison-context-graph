import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from main import app, context_service  # noqa: E402


def test_actuation_telemetry_records():
    client = TestClient(app)
    payload = {
        "action_id": "a-1",
        "person_id": "person-1",
        "device_id": "light-1",
        "device_class": "light",
        "intent": "turn_on",
        "status": "completed",
    }
    resp = client.post("/telemetry/actuation", json=payload)
    assert resp.status_code == 200
    # Verify it was stored in replay list
    traces = context_service._sqlite_replay.list("person-1").traces
    assert any(t.event == "actuation.lifecycle" for t in traces)
