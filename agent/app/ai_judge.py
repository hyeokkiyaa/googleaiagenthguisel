"""Mock sLM-style context judge for the MVP demo cases."""

import re

from agent.app.schemas import AIResult

EmailPattern = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
PhonePattern = re.compile(r"\b01[016789]-?\d{3,4}-?\d{4}\b")
RrnPattern = re.compile(r"(?<!\d)\d{6}-[1-4]\d{6}(?!\d)")

ResumeContextPattern = re.compile(
    r"(이력서|본인|개인|resume|my own|personal)",
    re.IGNORECASE,
)
InternalCodePattern = re.compile(
    r"(TraceForge[A-Za-z0-9_]*|[A-Za-z0-9_]*PolicyResolver|"
    r"[A-Za-z0-9_]*RiskScorer[A-Za-z0-9_]*|"
    r"hf_internal_[A-Za-z0-9_]*|internal_[A-Za-z0-9_]*|"
    r"[A-Za-z0-9_]*pricing_engine)",
    re.IGNORECASE,
)

ExternalEmailSurfaces = {"gmail", "external_email", "demo_gmail"}
ExternalAISurfaces = {"chatgpt", "claude", "gemini", "external_llm"}


def analyze_ai_judge(content: str, surface: str) -> AIResult:
    normalized_surface = surface.lower()

    if _looks_like_own_resume_pii(content):
        return AIResult(
            decision="PASS",
            reason="The content appears to be the user's own resume context rather than company or customer data.",
            evidence=["own_pii_resume_context"],
        )

    if _looks_like_customer_contact_list(content):
        evidence = ["customer_contact_list_pattern"]
        if normalized_surface in ExternalEmailSurfaces:
            evidence.append("external_email_surface")

        return AIResult(
            decision="BLOCK",
            reason="The content looks like a customer or sales lead contact list in an external transfer context.",
            evidence=evidence,
        )

    if InternalCodePattern.search(content):
        evidence = ["internal_code_identifier"]
        if normalized_surface in ExternalAISurfaces:
            evidence.append("external_ai_surface")

        return AIResult(
            decision="BLOCK",
            reason="The content contains internal code or product identifiers that should not be sent to an external AI tool.",
            evidence=evidence,
        )

    return AIResult(
        decision="PASS",
        reason="No risky business, customer, personal, or internal code context was detected.",
        evidence=["no_risky_context_detected"],
    )


def _looks_like_own_resume_pii(content: str) -> bool:
    return bool(RrnPattern.search(content) and ResumeContextPattern.search(content))


def _looks_like_customer_contact_list(content: str) -> bool:
    email_count = len(EmailPattern.findall(content))
    phone_count = len(PhonePattern.findall(content))
    line_count = len([line for line in content.splitlines() if line.strip()])
    business_terms = ("company", "manager", "cto", "buyer", "sales", "procurement")
    has_business_terms = any(term in content.lower() for term in business_terms)

    return email_count >= 3 and phone_count >= 3 and line_count >= 3 and has_business_terms
