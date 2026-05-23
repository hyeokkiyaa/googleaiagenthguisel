from agent.app.rule_dlp import analyze_rule_dlp


def test_resident_registration_number_is_blocked() -> None:
    result = analyze_rule_dlp("이력서 주민등록번호 950101-1234567")

    assert result.decision == "BLOCK"
    assert "resident_registration_number" in result.matched_rules
    assert result.reason


def test_confidential_keyword_is_warned() -> None:
    result = analyze_rule_dlp("This document contains confidential roadmap notes.")

    assert result.decision == "WARN"
    assert "confidential_keyword" in result.matched_rules
    assert result.reason


def test_plain_text_passes() -> None:
    result = analyze_rule_dlp("일반적인 점심 메뉴 논의입니다.")

    assert result.decision == "PASS"
    assert result.matched_rules == []


def test_customer_lead_list_without_rrn_passes_rule_baseline() -> None:
    content = "\n".join(
        [
            "김민준, Acme Korea, Sales Manager, minjun.kim@example.com, 010-1111-2222",
            "이지우, Beta Labs, CTO, jiwoo.lee@example.com, 010-3333-4444",
            "박서연, Cloud Nine, Buyer, seoyeon.park@example.com, 010-5555-6666",
        ]
    )

    result = analyze_rule_dlp(content)

    assert result.decision == "PASS"
    assert result.matched_rules == []


def test_internal_function_name_passes_rule_baseline() -> None:
    content = "TraceForgePolicyResolver calls customerRiskScorerV2 during debugging."

    result = analyze_rule_dlp(content)

    assert result.decision == "PASS"
    assert result.matched_rules == []

