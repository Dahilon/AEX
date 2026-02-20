"""
Shock injection routes.
"""

import json
import logging
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from backend.services.market_engine.models import ShockType
from backend.services.observability.metrics import emit_shock_metric, flush_metrics
from backend.services.observability.events import emit_shock_event
from .market import manager

logger = logging.getLogger(__name__)
router = APIRouter()


class InjectShockRequest(BaseModel):
    shock_type: ShockType
    severity: float | None = Field(None, ge=0.0, le=1.0)
    description: str | None = None


@router.post("/inject")
async def inject_shock(body: InjectShockRequest, request: Request) -> dict:
    """
    Inject a market shock event.
    Shock propagates over the next 4 market ticks with decay.
    """
    engine = request.app.state.engine

    shock = engine.inject_shock(
        shock_type=body.shock_type,
        severity=body.severity,
        description=body.description,
        source="manual",
    )

    shock_dict = shock.to_dict()
    agent_count = len(engine.state.agents)

    emit_shock_metric(shock_dict, impacted_agents=agent_count)
    emit_shock_event(shock_dict, agent_count=agent_count)
    flush_metrics()

    await manager.broadcast({
        "type": "shock",
        "shock": shock_dict,
    })

    return shock_dict
