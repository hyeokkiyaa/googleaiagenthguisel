"""FastAPI entrypoint for the ContextGuard local agent."""

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent.app import __version__
from agent.app.ai_provider import analyze_ai_with_provider
from agent.app.incidents import IncidentStore, build_incident
from agent.app.policy import decide_policy
from agent.app.rule_dlp import analyze_rule_dlp
from agent.app.schemas import AnalyzeRequest, AnalyzeResponse, Incident, MetricsResponse

_MOCK_DATA_PATH = Path("dashboard/mock_data.json")

incident_store = IncidentStore()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if not incident_store.list_incidents() and _MOCK_DATA_PATH.exists():
        with _MOCK_DATA_PATH.open("r", encoding="utf-8") as f:
            mock = json.load(f)
        # Store oldest-first so list_incidents() (which reverses) returns newest-first
        seed = [Incident.model_validate(i) for i in reversed(mock["incidents"])]
        incident_store._write_all(seed)
    yield


app = FastAPI(
    title="ContextGuard Local Agent",
    version=__version__,
    lifespan=lifespan,
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
    ai_result = analyze_ai_with_provider(request.content, request.surface)
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
