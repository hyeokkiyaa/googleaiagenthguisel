from pathlib import Path

from agent.app.incidents import IncidentStore, build_incident
from agent.app.schemas import AIResult, AnalyzeRequest, PolicyResult, ProductivityImpact, RuleResult


def _request(content: str = "sample content") -> AnalyzeRequest:
    return AnalyzeRequest(
        source="chrome_extension",
        surface="gmail",
        event_type="browser_paste",
        content_type="text",
        content=content,
    )


def _rule(decision: str = "PASS") -> RuleResult:
    return RuleResult(decision=decision, matched_rules=[], reason="rule reason")


def _ai(decision: str = "BLOCK") -> AIResult:
    return AIResult(decision=decision, reason="ai reason", evidence=["evidence"])


def _policy(decision: str = "BLOCK") -> PolicyResult:
    return PolicyResult(
        decision=decision,
        risk_level="high",
        final_reason="final reason",
        productivity_impact=ProductivityImpact(
            rule_only_outcome="PASS",
            contextguard_outcome=decision,
            impact_type="prevented_false_negative" if decision == "BLOCK" else "none",
        ),
    )


def test_warn_or_block_decision_is_saved(tmp_path: Path) -> None:
    store = IncidentStore(tmp_path / "incidents.json")
    incident = build_incident(_request(), _rule(), _ai(), _policy("BLOCK"))

    saved = store.save_decision(incident)

    assert saved is not None
    assert saved.id == "inc_000001"
    assert store.list_incidents()[0].id == "inc_000001"


def test_pass_decision_is_not_saved_as_incident(tmp_path: Path) -> None:
    store = IncidentStore(tmp_path / "incidents.json")
    incident = build_incident(
        _request(),
        _rule("PASS"),
        AIResult(
            decision="PASS",
            reason="safe",
            evidence=["no_risky_context_detected"],
        ),
        _policy("PASS"),
    )

    saved = store.save_decision(incident)

    assert saved is None
    assert store.list_incidents() == []


def test_raw_content_is_redacted(tmp_path: Path) -> None:
    store = IncidentStore(tmp_path / "incidents.json")
    incident = build_incident(
        _request("주민등록번호 950101-1234567, minjun.kim@example.com, 010-1111-2222"),
        _rule("BLOCK"),
        _ai("BLOCK"),
        _policy("BLOCK"),
    )

    saved = store.save_decision(incident)

    assert saved is not None
    assert "950101-1234567" not in saved.raw_sample_redacted
    assert "minjun.kim@example.com" not in saved.raw_sample_redacted
    assert "010-1111-2222" not in saved.raw_sample_redacted
    assert "[RRN]" in saved.raw_sample_redacted
    assert "[EMAIL]" in saved.raw_sample_redacted
    assert "[PHONE]" in saved.raw_sample_redacted


def test_incident_list_returns_latest_first(tmp_path: Path) -> None:
    store = IncidentStore(tmp_path / "incidents.json")

    first = store.save_decision(build_incident(_request("first"), _rule(), _ai(), _policy("WARN")))
    second = store.save_decision(build_incident(_request("second"), _rule(), _ai(), _policy("BLOCK")))

    incidents = store.list_incidents()

    assert first is not None
    assert second is not None
    assert [incident.id for incident in incidents] == ["inc_000002", "inc_000001"]


def test_metrics_are_calculated_from_saved_incidents(tmp_path: Path) -> None:
    store = IncidentStore(tmp_path / "incidents.json")

    store.save_decision(build_incident(_request("warn"), _rule("BLOCK"), _ai("PASS"), _policy("WARN")))
    store.save_decision(build_incident(_request("block"), _rule(), _ai("BLOCK"), _policy("BLOCK")))

    metrics = store.metrics()

    assert metrics == {
        "total": 2,
        "pass": 0,
        "warn": 1,
        "block": 1,
        "prevented_false_positive": 0,
        "prevented_false_negative": 1,
        "manual_review_saved": 0,
    }

