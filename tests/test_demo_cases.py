from pathlib import Path

from agent.app.ai_judge import analyze_ai_judge
from agent.app.policy import decide_policy
from agent.app.rule_dlp import analyze_rule_dlp

SamplesDir = Path("demo/samples")


def _read_sample(name: str) -> str:
    return (SamplesDir / name).read_text(encoding="utf-8")


def test_case_a_resume_sample_matches_expected_decision() -> None:
    content = _read_sample("case_a_resume.txt")

    rule_result = analyze_rule_dlp(content)
    ai_result = analyze_ai_judge(content, surface="demo_upload")
    policy_result = decide_policy(rule_result, ai_result)

    assert rule_result.decision == "BLOCK"
    assert ai_result.decision == "PASS"
    assert policy_result.decision == "WARN"
    assert policy_result.productivity_impact.impact_type == "prevented_false_positive"


def test_case_b_customer_leads_sample_matches_expected_decision() -> None:
    content = _read_sample("case_b_customer_leads.csv")

    rule_result = analyze_rule_dlp(content)
    ai_result = analyze_ai_judge(content, surface="gmail")
    policy_result = decide_policy(rule_result, ai_result)

    assert rule_result.decision == "PASS"
    assert ai_result.decision == "BLOCK"
    assert policy_result.decision == "BLOCK"
    assert policy_result.risk_level == "critical"
    assert policy_result.productivity_impact.impact_type == "prevented_false_negative"


def test_case_c_internal_code_sample_matches_expected_decision() -> None:
    content = _read_sample("case_c_internal_code.txt")

    rule_result = analyze_rule_dlp(content)
    ai_result = analyze_ai_judge(content, surface="chatgpt")
    policy_result = decide_policy(rule_result, ai_result)

    assert rule_result.decision == "PASS"
    assert ai_result.decision == "BLOCK"
    assert policy_result.decision == "BLOCK"
    assert policy_result.risk_level == "high"
    assert policy_result.productivity_impact.impact_type == "prevented_false_negative"


def test_demo_samples_are_marked_as_synthetic() -> None:
    for path in SamplesDir.glob("*"):
        assert "SYNTHETIC DEMO DATA" in path.read_text(encoding="utf-8")

