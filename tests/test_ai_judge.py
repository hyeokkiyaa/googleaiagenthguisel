from agent.app.ai_judge import analyze_ai_judge


def test_resume_with_own_pii_is_not_blocked_by_ai() -> None:
    result = analyze_ai_judge(
        content="개인 이력서입니다. 본인 확인용 주민등록번호 950101-1234567을 적었습니다.",
        surface="demo_upload",
    )

    assert result.decision in {"PASS", "WARN"}
    assert "own_pii_resume_context" in result.evidence
    assert result.reason


def test_customer_contact_list_is_blocked_by_ai() -> None:
    content = "\n".join(
        [
            "김민준, Acme Korea, Sales Manager, minjun.kim@example.com, 010-1111-2222",
            "이지우, Beta Labs, CTO, jiwoo.lee@example.com, 010-3333-4444",
            "박서연, Cloud Nine, Buyer, seoyeon.park@example.com, 010-5555-6666",
            "최도윤, Delta Works, Procurement, doyoon.choi@example.com, 010-7777-8888",
        ]
    )

    result = analyze_ai_judge(content=content, surface="gmail")

    assert result.decision == "BLOCK"
    assert "customer_contact_list_pattern" in result.evidence
    assert "external_email_surface" in result.evidence
    assert result.reason


def test_internal_code_identifier_is_blocked_by_ai() -> None:
    result = analyze_ai_judge(
        content="Debug TraceForgePolicyResolver and customerRiskScorerV2 in hf_internal_pricing_engine.",
        surface="chatgpt",
    )

    assert result.decision == "BLOCK"
    assert "internal_code_identifier" in result.evidence
    assert "external_ai_surface" in result.evidence
    assert result.reason


def test_general_question_passes_ai_judge() -> None:
    result = analyze_ai_judge(
        content="파이썬에서 리스트를 정렬하는 방법을 알려줘.",
        surface="chatgpt",
    )

    assert result.decision == "PASS"
    assert result.evidence == ["no_risky_context_detected"]
    assert result.reason


def test_ai_judge_always_returns_reason_and_evidence() -> None:
    samples = [
        ("개인 이력서 본인 주민등록번호 950101-1234567", "demo_upload"),
        ("김민준, Acme Korea, minjun.kim@example.com, 010-1111-2222", "gmail"),
        ("TraceForgePolicyResolver debugging", "chatgpt"),
        ("hello world", "chatgpt"),
    ]

    for content, surface in samples:
        result = analyze_ai_judge(content=content, surface=surface)

        assert result.reason
        assert result.evidence

