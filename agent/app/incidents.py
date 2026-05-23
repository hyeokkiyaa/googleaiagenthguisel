"""File-backed incident storage for the local MVP."""

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from agent.app.schemas import AIResult, AnalyzeRequest, Incident, PolicyResult, RuleResult

DefaultIncidentPath = Path("agent/data/incidents.json")
RrnPattern = re.compile(r"(?<!\d)\d{6}-[1-4]\d{6}(?!\d)")
EmailPattern = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
PhonePattern = re.compile(r"\b01[016789]-?\d{3,4}-?\d{4}\b")


class IncidentStore:
    def __init__(self, path: Path = DefaultIncidentPath) -> None:
        self.path = path

    def save_decision(self, incident: Incident) -> Incident | None:
        if incident.decision == "PASS":
            return None

        incidents = self._read_all()
        incident.id = self._next_id(incidents)
        incident.created_at = datetime.now(UTC).isoformat()
        incidents.append(incident)
        self._write_all(incidents)
        return incident

    def list_incidents(self) -> list[Incident]:
        return list(reversed(self._read_all()))

    def metrics(self) -> dict[str, int]:
        incidents = self._read_all()
        metrics = {
            "total": len(incidents),
            "pass": 0,
            "warn": 0,
            "block": 0,
            "prevented_false_positive": 0,
            "prevented_false_negative": 0,
            "manual_review_saved": 0,
        }

        for incident in incidents:
            if incident.decision == "PASS":
                metrics["pass"] += 1
            elif incident.decision == "WARN":
                metrics["warn"] += 1
            elif incident.decision == "BLOCK":
                metrics["block"] += 1

            impact_type = incident.productivity_impact.impact_type
            if impact_type in metrics:
                metrics[impact_type] += 1

        return metrics

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()

    def _read_all(self) -> list[Incident]:
        if not self.path.exists():
            return []

        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return [Incident.model_validate(item) for item in data]

    def _write_all(self, incidents: list[Incident]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [incident.model_dump(mode="json") for incident in incidents]

        with self.path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    @staticmethod
    def _next_id(incidents: list[Incident]) -> str:
        return f"inc_{len(incidents) + 1:06d}"


def build_incident(
    request: AnalyzeRequest,
    rule_result: RuleResult,
    ai_result: AIResult,
    policy_result: PolicyResult,
) -> Incident:
    return Incident(
        source=request.source,
        surface=request.surface,
        event_type=request.event_type,
        decision=policy_result.decision,
        risk_level=policy_result.risk_level,
        rule_decision=rule_result.decision,
        ai_decision=ai_result.decision,
        title=_title(policy_result),
        summary=_summary(request, policy_result),
        evidence=[*rule_result.matched_rules, *ai_result.evidence],
        final_reason=policy_result.final_reason,
        productivity_impact=policy_result.productivity_impact,
        raw_sample_redacted=redact_content(request.content),
    )


def redact_content(content: str, max_length: int = 240) -> str:
    redacted = RrnPattern.sub("[RRN]", content)
    redacted = EmailPattern.sub("[EMAIL]", redacted)
    redacted = PhonePattern.sub("[PHONE]", redacted)
    redacted = " ".join(redacted.split())

    if len(redacted) <= max_length:
        return redacted

    return f"{redacted[:max_length].rstrip()}..."


def _title(policy_result: PolicyResult) -> str:
    if policy_result.decision == "BLOCK":
        return "Risky external action blocked"
    if policy_result.decision == "WARN":
        return "Risky external action requires review"
    return "Action passed"


def _summary(request: AnalyzeRequest, policy_result: PolicyResult) -> str:
    return (
        f"{request.source} reported {request.event_type} on {request.surface}; "
        f"ContextGuard decided {policy_result.decision}."
    )

