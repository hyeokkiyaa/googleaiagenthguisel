"""AI judge provider selection for mock and Gemini-backed analysis."""

import json
import os
from typing import Any

import httpx
from pydantic import ValidationError

from agent.app.ai_judge import analyze_ai_judge as analyze_mock_ai_judge
from agent.app.schemas import AIResult


class GeminiProviderError(RuntimeError):
    """Raised when Gemini cannot return a valid AIResult."""


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

        text = _extract_text(response.json())
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise GeminiProviderError("Gemini response was not valid JSON") from exc

        try:
            return AIResult.model_validate(data)
        except ValidationError as exc:
            raise GeminiProviderError("Gemini JSON did not match AIResult schema") from exc

    @staticmethod
    def _request_body(content: str, surface: str) -> dict[str, Any]:
        prompt = f"""
You are ContextGuard's local AI risk judge.

Return ONLY compact JSON matching this schema:
{{
  "decision": "PASS" | "WARN" | "BLOCK",
  "reason": "short reason",
  "evidence": ["short evidence labels"]
}}

Decision policy:
- PASS: normal work or clearly personal own data in a non-external-transfer context.
- WARN: ambiguous personal or business context that should be reviewed.
- BLOCK: customer database, confidential business data, internal code identifiers, or company IP sent to external email/AI/upload surfaces.

Surface: {surface}
Content:
{content}
""".strip()

        return {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
            },
        }


def analyze_ai_with_provider(content: str, surface: str) -> AIResult:
    provider = os.getenv("CONTEXTGUARD_AI_PROVIDER", "mock").strip().lower()

    if provider != "gemini":
        return analyze_mock_ai_judge(content, surface)

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


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise GeminiProviderError(f"{name} is required for Gemini provider")
    return value


def _extract_text(payload: dict[str, Any]) -> str:
    try:
        return payload["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GeminiProviderError("Gemini response did not include text content") from exc

