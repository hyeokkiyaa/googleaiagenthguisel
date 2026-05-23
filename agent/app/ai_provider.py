"""AI judge provider selection for mock, Gemini, and Claude-backed analysis."""

import json
import os
import re
from typing import Any

import httpx
from dotenv import load_dotenv
from pydantic import ValidationError

from agent.app.ai_judge import analyze_ai_judge as analyze_mock_ai_judge
from agent.app.schemas import AIResult

load_dotenv()


class GeminiProviderError(RuntimeError):
    """Raised when Gemini cannot return a valid AIResult."""


class ClaudeProviderError(RuntimeError):
    """Raised when Claude cannot return a valid AIResult."""


PromptTemplate = """
You are ContextGuard's local AI risk judge.

Return ONLY compact JSON matching this schema:
{{
  "decision": "PASS" | "WARN" | "BLOCK",
  "reason": "short reason",
  "evidence": ["short evidence labels"]
}}

Decision policy:
- PASS: normal work content, public information, or clearly personal own data in a safe context.
- WARN: ambiguous personal or business context that should be reviewed before proceeding.
- BLOCK: any of the following must result in BLOCK with no exceptions:
  * API keys, secret keys, access tokens (e.g. sk-proj-..., AWS_SECRET_ACCESS_KEY, Bearer tokens)
  * Database connection strings with credentials (e.g. mysql://user:pass@host)
  * Cloud provider credentials (AWS, GCP, Azure keys)
  * Private keys, certificates, or authentication secrets
  * Customer PII databases, confidential business data, or company IP

Surface: {surface}
Content:
{content}
""".strip()


class GeminiAIJudge:
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        api_base: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: float = 8.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.api_base = api_base.rstrip("/")
        self.client = client or httpx.Client(timeout=timeout_seconds)

    def analyze(self, content: str, surface: str) -> AIResult:
        response = self.client.post(
            f"{self.api_base}/models/{self.model}:generateContent",
            params={"key": self.api_key},
            json=self._request_body(content=content, surface=surface),
        )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise GeminiProviderError(f"Gemini HTTP error: {exc.response.status_code}") from exc

        return _parse_ai_result(
            text=_extract_gemini_text(response.json()),
            error_type=GeminiProviderError,
            provider_name="Gemini",
        )

    @staticmethod
    def _request_body(content: str, surface: str) -> dict[str, Any]:
        return {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": PromptTemplate.format(surface=surface, content=content)}],
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
            },
        }


class ClaudeAIJudge:
    def __init__(
        self,
        api_key: str,
        model: str = "claude-haiku-4-5-20251001",
        api_base: str = "https://api.anthropic.com/v1",
        timeout_seconds: float = 8.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.api_base = api_base.rstrip("/")
        self.client = client or httpx.Client(timeout=timeout_seconds)

    def analyze(self, content: str, surface: str) -> AIResult:
        response = self.client.post(
            f"{self.api_base}/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=self._request_body(content=content, surface=surface),
        )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ClaudeProviderError(f"Claude HTTP error: {exc.response.status_code}") from exc

        return _parse_ai_result(
            text=_extract_claude_text(response.json()),
            error_type=ClaudeProviderError,
            provider_name="Claude",
        )

    def _request_body(self, content: str, surface: str) -> dict[str, Any]:
        return {
            "model": self.model,
            "max_tokens": 300,
            "temperature": 0,
            "messages": [
                {
                    "role": "user",
                    "content": PromptTemplate.format(surface=surface, content=content),
                }
            ],
        }


def analyze_ai_with_provider(content: str, surface: str) -> AIResult:
    provider = os.getenv("CONTEXTGUARD_AI_PROVIDER", "mock").strip().lower()

    if provider == "mock":
        return analyze_mock_ai_judge(content, surface)

    if provider == "gemini":
        return _analyze_with_gemini(content=content, surface=surface)

    if provider == "claude":
        return _analyze_with_claude(content=content, surface=surface)

    fallback = analyze_mock_ai_judge(content, surface)
    return AIResult(
        decision=fallback.decision,
        reason=f"Unknown AI provider '{provider}'; fallback to mock AI Judge. {fallback.reason}",
        evidence=["provider_fallback", *fallback.evidence],
    )


def _analyze_with_gemini(content: str, surface: str) -> AIResult:
    try:
        gemini = GeminiAIJudge(
            api_key=_required_env("GEMINI_API_KEY"),
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            api_base=os.getenv(
                "GEMINI_API_BASE",
                "https://generativelanguage.googleapis.com/v1beta",
            ),
            timeout_seconds=float(os.getenv("GEMINI_TIMEOUT_SECONDS", "8")),
        )
        return gemini.analyze(content=content, surface=surface)
    except (GeminiProviderError, httpx.HTTPError, ValueError) as exc:
        fallback = analyze_mock_ai_judge(content, surface)
        return AIResult(
            decision=fallback.decision,
            reason=f"Gemini unavailable; fallback to mock AI Judge. {fallback.reason}",
            evidence=["gemini_fallback", *fallback.evidence],
        )


def _analyze_with_claude(content: str, surface: str) -> AIResult:
    try:
        claude = ClaudeAIJudge(
            api_key=_first_env("ANTHROPIC_API_KEY", "CLAUDE_API_KEY"),
            model=os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001"),
            api_base=os.getenv("CLAUDE_API_BASE", "https://api.anthropic.com/v1"),
            timeout_seconds=float(os.getenv("CLAUDE_TIMEOUT_SECONDS", "8")),
        )
        return claude.analyze(content=content, surface=surface)
    except (ClaudeProviderError, httpx.HTTPError, ValueError) as exc:
        fallback = analyze_mock_ai_judge(content, surface)
        return AIResult(
            decision=fallback.decision,
            reason=f"Claude unavailable; fallback to mock AI Judge. {fallback.reason}",
            evidence=["claude_fallback", *fallback.evidence],
        )


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise GeminiProviderError(f"{name} is required for Gemini provider")
    return value


def _first_env(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    joined_names = " or ".join(names)
    raise ClaudeProviderError(f"{joined_names} is required for Claude provider")


def _extract_gemini_text(payload: dict[str, Any]) -> str:
    try:
        return payload["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GeminiProviderError("Gemini response did not include text content") from exc


def _extract_claude_text(payload: dict[str, Any]) -> str:
    try:
        content_blocks = payload["content"]
        text_parts = [
            block["text"]
            for block in content_blocks
            if block.get("type") == "text" and block.get("text")
        ]
        if not text_parts:
            raise KeyError("no text content")
        return "\n".join(text_parts)
    except (KeyError, TypeError) as exc:
        raise ClaudeProviderError("Claude response did not include text content") from exc


def _parse_ai_result(
    text: str,
    error_type: type[RuntimeError],
    provider_name: str,
) -> AIResult:
    json_text = _extract_json_text(text)

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise error_type(f"{provider_name} response was not valid JSON") from exc

    try:
        return AIResult.model_validate(data)
    except ValidationError as exc:
        raise error_type(f"{provider_name} JSON did not match AIResult schema") from exc


def _extract_json_text(text: str) -> str:
    stripped = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, re.DOTALL)
    if fenced:
        return fenced.group(1)

    object_match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if object_match:
        return object_match.group(0)

    return stripped
