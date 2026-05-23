"""Rule-based DLP baseline checks."""

import re

from agent.app.schemas import RuleResult

RrnPattern = re.compile(r"\b\d{6}-[1-4]\d{6}\b")
ConfidentialKeywordPattern = re.compile(
    r"\b(confidential|secret|proprietary|classified)\b",
    re.IGNORECASE,
)


def analyze_rule_dlp(content: str) -> RuleResult:
    matched_rules: list[str] = []

    if RrnPattern.search(content):
        matched_rules.append("resident_registration_number")

    if ConfidentialKeywordPattern.search(content):
        matched_rules.append("confidential_keyword")

    if "resident_registration_number" in matched_rules:
        return RuleResult(
            decision="BLOCK",
            matched_rules=matched_rules,
            reason="Resident registration number pattern detected.",
        )

    if "confidential_keyword" in matched_rules:
        return RuleResult(
            decision="WARN",
            matched_rules=matched_rules,
            reason="Confidential keyword detected by rule baseline.",
        )

    return RuleResult(
        decision="PASS",
        matched_rules=[],
        reason="No rule DLP pattern matched.",
    )

