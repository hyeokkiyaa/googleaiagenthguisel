"""Policy decision engine combining rule and AI risk results."""

from agent.app.rule_dlp import HARD_BLOCK_RULES
from agent.app.schemas import AIResult, PolicyResult, ProductivityImpact, RuleResult


def decide_policy(rule_result: RuleResult, ai_result: AIResult) -> PolicyResult:
    hard_block = any(r in HARD_BLOCK_RULES for r in rule_result.matched_rules)

    if ai_result.decision == "BLOCK":
        decision = "BLOCK"
        risk_level = _blocked_risk_level(ai_result)
    elif rule_result.decision == "BLOCK" and hard_block:
        # Credentials/secrets: AI cannot override — always BLOCK
        decision = "BLOCK"
        risk_level = "critical"
    elif rule_result.decision == "BLOCK" and ai_result.decision in ("PASS", "WARN"):
        # AI didn't confirm full block (e.g. own tax docs) — downgrade to WARN
        decision = "WARN"
        risk_level = "medium"
    elif rule_result.decision == "WARN" and ai_result.decision == "PASS":
        decision = "WARN"
        risk_level = "medium"
    elif rule_result.decision == "BLOCK":
        decision = "BLOCK"
        risk_level = "high"
    else:
        decision = "PASS"
        risk_level = "low"

    return PolicyResult(
        decision=decision,
        risk_level=risk_level,
        final_reason=_final_reason(rule_result, ai_result, decision),
        productivity_impact=ProductivityImpact(
            rule_only_outcome=rule_result.decision,
            contextguard_outcome=decision,
            impact_type=_impact_type(rule_result, ai_result, decision),
        ),
    )


def _blocked_risk_level(ai_result: AIResult) -> str:
    if "customer_contact_list_pattern" in ai_result.evidence:
        return "critical"
    return "high"


def _impact_type(rule_result: RuleResult, ai_result: AIResult, decision: str) -> str:
    if rule_result.decision == "BLOCK" and ai_result.decision == "PASS" and decision != "BLOCK":
        return "prevented_false_positive"
    if rule_result.decision == "PASS" and ai_result.decision == "BLOCK" and decision == "BLOCK":
        return "prevented_false_negative"
    return "none"


def _final_reason(rule_result: RuleResult, ai_result: AIResult, decision: str) -> str:
    if decision == "BLOCK" and ai_result.decision == "BLOCK":
        return f"AI Judge blocked the action: {ai_result.reason}"
    if decision == "BLOCK":
        return f"Rule engine blocked: {rule_result.reason}"
    if decision == "WARN" and rule_result.decision == "BLOCK" and ai_result.decision in ("PASS", "WARN"):
        return "Rule DLP found a sensitive pattern, but AI Judge identified a lower-risk personal context."
    if decision == "WARN":
        return f"Rule DLP requested caution: {rule_result.reason}"
    return "Rule DLP and AI Judge both allowed the action."

