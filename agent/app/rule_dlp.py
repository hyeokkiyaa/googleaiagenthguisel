"""Rule-based DLP baseline checks."""

import re

from agent.app.schemas import RuleResult

RrnPattern = re.compile(r"(?<!\d)\d{6}-[1-4]\d{6}(?!\d)")
ConfidentialKeywordPattern = re.compile(
    r"\b(confidential|secret|proprietary|classified)\b",
    re.IGNORECASE,
)
ApiCredentialPattern = re.compile(
    r"(sk-proj-[A-Za-z0-9_-]{10,}"
    r"|AKIA[0-9A-Z]{16,}"
    r"|AWS_SECRET_ACCESS_KEY\s*=\s*\S+"
    r"|ghp_[A-Za-z0-9]{36,}"
    r"|[A-Za-z_]*(api[_-]?key|access[_-]?key|secret[_-]?key)\s*[=:]\s*\S{8,})",
    re.IGNORECASE,
)
DbCredentialPattern = re.compile(
    r"(mysql|postgresql|postgres|mongodb|redis)://[^@\s]+:[^@\s]+@",
    re.IGNORECASE,
)

# Rules that cannot be downgraded by AI PASS — always hard BLOCK
HARD_BLOCK_RULES = frozenset({"api_credential", "db_credential"})


def analyze_rule_dlp(content: str) -> RuleResult:
    matched_rules: list[str] = []

    if ApiCredentialPattern.search(content):
        matched_rules.append("api_credential")

    if DbCredentialPattern.search(content):
        matched_rules.append("db_credential")

    if RrnPattern.search(content):
        matched_rules.append("resident_registration_number")

    if ConfidentialKeywordPattern.search(content):
        matched_rules.append("confidential_keyword")

    if matched_rules and any(r in HARD_BLOCK_RULES for r in matched_rules):
        return RuleResult(
            decision="BLOCK",
            matched_rules=matched_rules,
            reason="Credential or connection string detected — hard block.",
        )

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
