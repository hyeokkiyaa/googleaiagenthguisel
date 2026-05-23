from agent.app.policy import decide_policy
from agent.app.schemas import AIResult, RuleResult


def test_rule_block_ai_pass_becomes_warn_with_false_positive_impact() -> None:
    result = decide_policy(
        rule_result=RuleResult(
            decision="BLOCK",
            matched_rules=["resident_registration_number"],
            reason="Resident registration number pattern detected.",
        ),
        ai_result=AIResult(
            decision="PASS",
            reason="Own resume context.",
            evidence=["own_pii_resume_context"],
        ),
    )

    assert result.decision == "WARN"
    assert result.risk_level == "medium"
    assert result.productivity_impact.impact_type == "prevented_false_positive"
    assert result.final_reason


def test_rule_pass_ai_block_becomes_block_with_false_negative_impact() -> None:
    result = decide_policy(
        rule_result=RuleResult(
            decision="PASS",
            matched_rules=[],
            reason="No rule DLP pattern matched.",
        ),
        ai_result=AIResult(
            decision="BLOCK",
            reason="Customer database context.",
            evidence=["customer_contact_list_pattern", "external_email_surface"],
        ),
    )

    assert result.decision == "BLOCK"
    assert result.risk_level == "critical"
    assert result.productivity_impact.impact_type == "prevented_false_negative"
    assert result.final_reason


def test_rule_block_ai_block_stays_block() -> None:
    result = decide_policy(
        rule_result=RuleResult(
            decision="BLOCK",
            matched_rules=["resident_registration_number"],
            reason="Resident registration number pattern detected.",
        ),
        ai_result=AIResult(
            decision="BLOCK",
            reason="Customer data context.",
            evidence=["customer_contact_list_pattern"],
        ),
    )

    assert result.decision == "BLOCK"
    assert result.risk_level == "critical"
    assert result.productivity_impact.impact_type == "none"


def test_rule_pass_ai_pass_stays_pass() -> None:
    result = decide_policy(
        rule_result=RuleResult(
            decision="PASS",
            matched_rules=[],
            reason="No rule DLP pattern matched.",
        ),
        ai_result=AIResult(
            decision="PASS",
            reason="No risky context.",
            evidence=["no_risky_context_detected"],
        ),
    )

    assert result.decision == "PASS"
    assert result.risk_level == "low"
    assert result.productivity_impact.impact_type == "none"


def test_internal_code_ai_block_is_high_risk() -> None:
    result = decide_policy(
        rule_result=RuleResult(
            decision="PASS",
            matched_rules=[],
            reason="No rule DLP pattern matched.",
        ),
        ai_result=AIResult(
            decision="BLOCK",
            reason="Internal code identifier.",
            evidence=["internal_code_identifier", "external_ai_surface"],
        ),
    )

    assert result.decision == "BLOCK"
    assert result.risk_level == "high"
    assert result.productivity_impact.impact_type == "prevented_false_negative"

