"""FastAPI entrypoint for the ContextGuard local agent."""

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent.app import __version__
from agent.app.ai_judge import analyze_ai_judge
from agent.app.incidents import IncidentStore, build_incident
from agent.app.policy import decide_policy
from agent.app.rule_dlp import analyze_rule_dlp
from agent.app.schemas import AnalyzeRequest, AnalyzeResponse, MetricsResponse

incident_store = IncidentStore()


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
    ai_result = analyze_ai_judge(request.content, request.surface)
    policy_result = decide_policy(rule_result, ai_result)
    incident = build_incident(request, rule_result, ai_result, policy_result)
    saved_incident = incident_store.save_decision(incident)

    return AnalyzeResponse(
        decision=policy_result.decision,
        risk_level=policy_result.risk_level,
        message="Rule DLP baseline, mock AI Judge, and policy decision applied.",
        rule_result=rule_result,
        ai_result=ai_result,
        final_reason=policy_result.final_reason,
        productivity_impact=policy_result.productivity_impact,
        incident_id=saved_incident.id if saved_incident else None,
    )


@app.get("/incidents")
def list_incidents() -> dict[str, list[dict[str, Any]]]:
    incidents = [
        incident.model_dump(mode="json")
        for incident in incident_store.list_incidents()
    ]
    return {"incidents": incidents}


@app.get("/metrics", response_model=MetricsResponse)
def metrics() -> MetricsResponse:
    return MetricsResponse(**incident_store.metrics())
