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
        "reason": "No risky business, customer, personal, or internal code context was detected.",
        "evidence": ["no_risky_context_detected"],
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


def test_analyze_case_a_resume_rrn_is_warned_as_false_positive_reduction() -> None:
    response = client.post(
        "/analyze",
        json={
            "source": "chrome_extension",
            "surface": "demo_upload",
            "event_type": "browser_paste",
            "content_type": "text",
            "content": "개인 이력서입니다. 본인 확인용 주민등록번호 950101-1234567을 적었습니다.",
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["rule_result"]["decision"] == "BLOCK"
    assert body["ai_result"]["decision"] == "PASS"
    assert body["decision"] == "WARN"
    assert body["productivity_impact"]["impact_type"] == "prevented_false_positive"


def test_analyze_case_b_customer_list_is_blocked_as_false_negative_reduction() -> None:
    content = "\n".join(
        [
            "김민준, Acme Korea, Sales Manager, minjun.kim@example.com, 010-1111-2222",
            "이지우, Beta Labs, CTO, jiwoo.lee@example.com, 010-3333-4444",
            "박서연, Cloud Nine, Buyer, seoyeon.park@example.com, 010-5555-6666",
            "최도윤, Delta Works, Procurement, doyoon.choi@example.com, 010-7777-8888",
        ]
    )

    response = client.post(
        "/analyze",
        json={
            "source": "chrome_extension",
            "surface": "gmail",
            "event_type": "browser_paste",
            "content_type": "text",
            "content": content,
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["rule_result"]["decision"] == "PASS"
    assert body["ai_result"]["decision"] == "BLOCK"
    assert body["decision"] == "BLOCK"
    assert body["risk_level"] == "critical"
    assert body["productivity_impact"]["impact_type"] == "prevented_false_negative"


def test_analyze_case_c_internal_code_is_blocked_as_false_negative_reduction() -> None:
    response = client.post(
        "/analyze",
        json={
            "source": "chrome_extension",
            "surface": "chatgpt",
            "event_type": "browser_paste",
            "content_type": "text",
            "content": "Debug TraceForgePolicyResolver and customerRiskScorerV2 in hf_internal_pricing_engine.",
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["rule_result"]["decision"] == "PASS"
    assert body["ai_result"]["decision"] == "BLOCK"
    assert body["decision"] == "BLOCK"
    assert body["risk_level"] == "high"
    assert body["productivity_impact"]["impact_type"] == "prevented_false_negative"
