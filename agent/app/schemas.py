"""Shared request and response schemas for the local agent."""

from typing import Any, Literal

from pydantic import BaseModel, Field

Decision = Literal["PASS", "WARN", "BLOCK"]
RiskLevel = Literal["low", "medium", "high", "critical"]


class AnalyzeRequest(BaseModel):
    source: str = Field(..., min_length=1)
    surface: str = Field(..., min_length=1)
    event_type: str = Field(..., min_length=1)
    content_type: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RuleResult(BaseModel):
    decision: Decision
    matched_rules: list[str]
    reason: str


class AIResult(BaseModel):
    decision: Decision
    reason: str
    evidence: list[str]


class AnalyzeResponse(BaseModel):
    decision: Decision
    risk_level: RiskLevel
    message: str
    rule_result: RuleResult
    ai_result: AIResult
    incident_id: str | None


class MetricsResponse(BaseModel):
    total: int
    pass_: int = Field(alias="pass")
    warn: int
    block: int
    prevented_false_positive: int
    prevented_false_negative: int
    manual_review_saved: int

