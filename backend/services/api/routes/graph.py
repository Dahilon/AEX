"""
Graph data routes — capital flow and contagion visualization.
"""

import logging
from fastapi import APIRouter, Request, Query
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/contagion")
async def get_contagion(
    request: Request,
    shock_id: Optional[str] = Query(None, description="Filter contagion path for specific shock"),
) -> dict:
    """
    Returns capital flow graph data.
    If shock_id is provided, returns the contagion path for that shock.
    Otherwise returns the full capital flow graph.
    """
    graph_service = request.app.state.graph_service
    try:
        data = graph_service.get_contagion_graph(shock_id=shock_id)
    except Exception as e:
        logger.warning(f"Graph query failed: {e}")
        data = {"nodes": [], "edges": [], "query_type": "error", "error": str(e)}
    return data


@router.get("/query/{query_type}")
async def run_graph_query(
    query_type: str,
    request: Request,
    shock_id: Optional[str] = Query(None),
    limit: int = Query(10),
) -> dict:
    """
    Run a named graph query. Returns raw results.
    query_type options: top_inflow, concentration_risk, contagion_path,
                        cross_sector_exposure, most_impacted_users
    """
    graph_service = request.app.state.graph_service
    params = {"limit": limit}
    if shock_id:
        params["shock_id"] = shock_id
    try:
        results = graph_service.run_query(query_type, params)
        return {"query_type": query_type, "results": results}
    except Exception as e:
        logger.error(f"Graph query error: {e}")
        return {"query_type": query_type, "results": [], "error": str(e)}
