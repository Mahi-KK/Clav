import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_index_renders_keyboard(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b'data-key="ShiftLeft"' in response.data


def test_analyze(client):
    response = client.post("/api/analyze", json={"text": "Hi!"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["keystrokes"] == 5
    assert body["shift_presses"] == 2


@pytest.mark.parametrize("payload", [None, [], {"text": 42}, {"words": "hi"}])
def test_analyze_rejects_bad_input(client, payload):
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_analyze_rejects_non_json(client):
    response = client.post("/api/analyze", data="hello", content_type="text/plain")
    assert response.status_code == 400


def test_analyze_rejects_huge_body(client):
    response = client.post("/api/analyze", json={"text": "a" * 200_000})
    assert response.status_code == 413


def test_unknown_route_returns_json(client):
    response = client.get("/nope")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Not found."}


def test_wrong_method_returns_json(client):
    response = client.get("/api/analyze")
    assert response.status_code == 405
