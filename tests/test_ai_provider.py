import httpx

from agent.app.ai_provider import (
    ClaudeAIJudge,
    ClaudeProviderError,
    GeminiAIJudge,
    GeminiProviderError,
    analyze_ai_with_provider,
)


def test_default_provider_uses_mock_judge(monkeypatch) -> None:
    monkeypatch.delenv("CONTEXTGUARD_AI_PROVIDER", raising=False)

    result = analyze_ai_with_provider(
        content="TraceForgePolicyResolver debugging",
        surface="chatgpt",
    )

    assert result.decision == "BLOCK"
    assert "internal_code_identifier" in result.evidence


def test_gemini_provider_without_api_key_falls_back_to_mock(monkeypatch) -> None:
    monkeypatch.setenv("CONTEXTGUARD_AI_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = analyze_ai_with_provider(
        content="TraceForgePolicyResolver debugging",
        surface="chatgpt",
    )

    assert result.decision == "BLOCK"
    assert result.evidence[0] == "gemini_fallback"
    assert "internal_code_identifier" in result.evidence


def test_claude_provider_without_api_key_falls_back_to_mock(monkeypatch) -> None:
    monkeypatch.setenv("CONTEXTGUARD_AI_PROVIDER", "claude")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("CLAUDE_API_KEY", raising=False)

    result = analyze_ai_with_provider(
        content="TraceForgePolicyResolver debugging",
        surface="chatgpt",
    )

    assert result.decision == "BLOCK"
    assert result.evidence[0] == "claude_fallback"
    assert "internal_code_identifier" in result.evidence


def test_gemini_provider_parses_json_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "key=test-key" in str(request.url)
        assert request.url.path.endswith("/models/gemini-test:generateContent")
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": (
                                        '{"decision":"BLOCK",'
                                        '"reason":"Customer lead list detected.",'
                                        '"evidence":["customer_contact_list_pattern"]}'
                                    )
                                }
                            ]
                        }
                    }
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = GeminiAIJudge(
        api_key="test-key",
        model="gemini-test",
        client=client,
    )

    result = provider.analyze(content="sample", surface="gmail")

    assert result.decision == "BLOCK"
    assert result.reason == "Customer lead list detected."
    assert result.evidence == ["customer_contact_list_pattern"]


def test_claude_provider_parses_json_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "test-key"
        assert request.headers["anthropic-version"] == "2023-06-01"
        assert request.url.path.endswith("/messages")
        payload = json_from_request(request)
        assert payload["model"] == "claude-test"
        return httpx.Response(
            200,
            json={
                "content": [
                    {
                        "type": "text",
                        "text": (
                            '{"decision":"BLOCK",'
                            '"reason":"Internal identifier detected.",'
                            '"evidence":["internal_code_identifier"]}'
                        ),
                    }
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = ClaudeAIJudge(
        api_key="test-key",
        model="claude-test",
        client=client,
    )

    result = provider.analyze(content="sample", surface="chatgpt")

    assert result.decision == "BLOCK"
    assert result.reason == "Internal identifier detected."
    assert result.evidence == ["internal_code_identifier"]


def test_gemini_provider_rejects_invalid_json_response() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json={
                    "candidates": [
                        {
                            "content": {
                                "parts": [{"text": "not-json"}],
                            },
                        }
                    ],
                },
            )
        )
    )
    provider = GeminiAIJudge(
        api_key="test-key",
        model="gemini-test",
        client=client,
    )

    try:
        provider.analyze(content="sample", surface="gmail")
    except GeminiProviderError as exc:
        assert "valid JSON" in str(exc)
    else:
        raise AssertionError("GeminiProviderError was not raised")


def test_claude_provider_rejects_invalid_json_response() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json={
                    "content": [
                        {
                            "type": "text",
                            "text": "not-json",
                        }
                    ],
                },
            )
        )
    )
    provider = ClaudeAIJudge(
        api_key="test-key",
        model="claude-test",
        client=client,
    )

    try:
        provider.analyze(content="sample", surface="gmail")
    except ClaudeProviderError as exc:
        assert "valid JSON" in str(exc)
    else:
        raise AssertionError("ClaudeProviderError was not raised")


def json_from_request(request: httpx.Request) -> dict:
    return __import__("json").loads(request.content.decode("utf-8"))
