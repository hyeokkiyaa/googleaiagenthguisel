"""FastAPI entrypoint for the ContextGuard local agent."""

from typing import Any, Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent.app import __version__

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


app = FastAPI(
    title="ContextGuard Local Agent",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_app_metadata() -> dict[str, str]:
    """Return basic metadata used by smoke tests and health checks."""
    return {
        "name": "ContextGuard Local Agent",
        "status": "ready",
        "version": __version__,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(_: AnalyzeRequest) -> AnalyzeResponse:
    return AnalyzeResponse(
        decision="PASS",
        risk_level="low",
        message="Analysis accepted. Risk engine is not implemented yet.",
        rule_result=RuleResult(
            decision="PASS",
            matched_rules=[],
            reason="Rule DLP is not implemented yet.",
        ),
        ai_result=AIResult(
            decision="PASS",
            reason="AI Judge is not implemented yet.",
            evidence=[],
        ),
        incident_id=None,
    )


@app.get("/incidents")
def list_incidents() -> dict[str, list[dict[str, Any]]]:
    return {"incidents": []}


@app.get("/metrics", response_model=MetricsResponse)
def metrics() -> MetricsResponse:
    return MetricsResponse(
        total=0,
        **{
            "pass": 0,
            "warn": 0,
            "block": 0,
            "prevented_false_positive": 0,
            "prevented_false_negative": 0,
            "manual_review_saved": 0,
        },
    )
