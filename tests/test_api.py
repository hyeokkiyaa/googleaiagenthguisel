from fastapi.testclient import TestClient

from agent.app.main import app


client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_returns_decision_schema_for_minimal_request() -> None:
    response = client.post(
        "/analyze",
        json={
            "source": "chrome_extension",
            "surface": "chatgpt",
            "event_type": "browser_paste",
            "content_type": "text",
            "content": "hello world",
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["decision"] == "PASS"
    assert body["risk_level"] == "low"
    assert body["message"]
    assert body["incident_id"] is None
    assert body["rule_result"] == {
        "decision": "PASS",
        "matched_rules": [],
        "reason": "No rule DLP pattern matched.",
    }
    assert body["ai_result"] == {
        "decision": "PASS",
        "reason": "AI Judge is not implemented yet.",
        "evidence": [],
    }


def test_analyze_rejects_invalid_request() -> None:
    response = client.post("/analyze", json={"content": "missing required fields"})

    assert response.status_code == 422


def test_cors_preflight_allows_browser_surfaces() -> None:
    response = client.options(
        "/analyze",
        headers={
            "Origin": "https://chat.openai.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"


def test_incidents_starts_empty() -> None:
    response = client.get("/incidents")

    assert response.status_code == 200
    assert response.json() == {"incidents": []}


def test_metrics_returns_default_values() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.json() == {
        "total": 0,
        "pass": 0,
        "warn": 0,
        "block": 0,
        "prevented_false_positive": 0,
        "prevented_false_negative": 0,
        "manual_review_saved": 0,
    }
