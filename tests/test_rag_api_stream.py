import json

from fastapi.testclient import TestClient

from nakshatra.api import app


def test_rag_ask_stream_lifecycle():
    client = TestClient(app)
    response = client.post(
        "/rag/ask/stream",
        json={"question": "What does Jupiter in 1st house signify?", "top_k": 2},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    events = []
    for line in response.text.split("\n\n"):
        line = line.strip()
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))

    event_types = [e.get("type") for e in events]
    assert "init" in event_types
    assert "done" in event_types
    # At least one token was yielded
    assert "token" in event_types
