"""FastAPI entrypoint for the ContextGuard local agent."""

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent.app import __version__
from agent.app.rule_dlp import analyze_rule_dlp
from agent.app.schemas import AIResult, AnalyzeRequest, AnalyzeResponse, MetricsResponse


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
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    rule_result = analyze_rule_dlp(request.content)
    risk_level = "medium" if rule_result.decision == "WARN" else "high"
    if rule_result.decision == "PASS":
        risk_level = "low"

    return AnalyzeResponse(
        decision=rule_result.decision,
        risk_level=risk_level,
        message="Rule DLP baseline applied. AI Judge is not implemented yet.",
        rule_result=rule_result,
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
