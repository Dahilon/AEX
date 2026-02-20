"""
Shock injection routes.
"""

import json
import logging
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from services.market_engine.models import ShockType
from services.observability.metrics import emit_shock_metric
from .market import manager  # reuse WS broadcast

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
    graph_service = request.app.state.graph_service

    shock = engine.inject_shock(
        shock_type=body.shock_type,
        severity=body.severity,
        description=body.description,
        source="manual",
    )

    shock_dict = shock.to_dict()

    # Emit Datadog metric
    emit_shock_metric(shock_dict, impacted_agents=len(engine.state.agents))

    # Persist shock to Neo4j (non-blocking, best-effort)
    try:
        graph_service.create_shock(shock_dict)
        # Link shock to all sectors with appropriate beta
        from services.shock_engine.sector_betas import get_beta, SECTOR_BETAS
        from services.market_engine.models import Sector
        sector_impacts = []
        for sector in Sector:
            beta = get_beta(shock.shock_type, sector)
            if beta != 0.0:
                sector_impacts.append({
                    "sector_id": sector.value,
                    "severity": shock.severity,
                    "direction": 1 if beta > 0 else -1,
                })
        graph_service.link_shock_to_sectors(shock.shock_id, sector_impacts)
    except Exception as e:
        logger.warning(f"Neo4j shock persist failed (non-fatal): {e}")

    # Broadcast shock event to all WebSocket clients
    await manager.broadcast({
        "type": "shock",
        "shock": shock_dict,
    })

    return shock_dict
