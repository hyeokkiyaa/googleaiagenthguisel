import httpx

from agent.app.ai_provider import GeminiAIJudge, GeminiProviderError, analyze_ai_with_provider


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

