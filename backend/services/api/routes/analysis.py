"""
Bedrock analysis routes: Market Analyst + Risk Agent.
"""

import logging
from fastapi import APIRouter, Request
from pydantic import BaseModel

from backend.services.observability.events import emit_analysis_event, emit_risk_event
from backend.services.observability.correlation import new_run_id

logger = logging.getLogger(__name__)
router = APIRouter()


class AnalysisRequest(BaseModel):
    question: str = "Analyze the current market state and explain what's happening."


@router.post("/run")
async def run_market_analyst(body: AnalysisRequest, request: Request) -> dict:
    run_id = new_run_id("analysis")
    agent = request.app.state.analyst_agent
    result = agent.analyze(user_question=body.question)
    emit_analysis_event("market_analyst", result)
    return result


@router.post("/risk")
async def run_risk_agent(request: Request) -> dict:
    run_id = new_run_id("risk")
    agent = request.app.state.risk_agent
    result = agent.analyze()
    emit_risk_event(result)
    return result
