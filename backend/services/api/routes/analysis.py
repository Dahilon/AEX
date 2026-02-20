"""
Bedrock analysis routes: Market Analyst + Risk Agent.
"""

import logging
from fastapi import APIRouter, Request
from pydantic import BaseModel

from backend.services.observability.events import emit_analysis_event, emit_risk_event

logger = logging.getLogger(__name__)
router = APIRouter()


class AnalysisRequest(BaseModel):
    question: str = "Analyze the current market state and explain what's happening."


@router.post("/run")
async def run_market_analyst(body: AnalysisRequest, request: Request) -> dict:
    """
    Run the Bedrock Market Analyst agent.
    Returns analysis text + token usage + latency.
    """
    agent = request.app.state.analyst_agent
    result = agent.analyze(user_question=body.question)
    emit_analysis_event("market_analyst", result)
    return result


@router.post("/risk")
async def run_risk_agent(request: Request) -> dict:
    """
    Run the Bedrock Risk Agent.
    Returns risk assessment text + risk_level.
    """
    agent = request.app.state.risk_agent
    result = agent.analyze()
    emit_risk_event(result)
    return result
