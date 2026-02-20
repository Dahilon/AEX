"""
Graph data routes — stub (Neo4j removed). Returns empty graph data for UI compatibility.
"""

from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()


@router.get("/contagion")
async def get_contagion(
    shock_id: Optional[str] = Query(None, description="Filter contagion path for specific shock"),
) -> dict:
    """Returns empty graph data (graph backend removed)."""
    return {
        "nodes": [],
        "edges": [],
        "query_type": "contagion_path" if shock_id else "top_inflow",
        "raw": [],
    }


@router.get("/query/{query_type}")
async def run_graph_query(
    query_type: str,
    shock_id: Optional[str] = Query(None),
    limit: int = Query(10),
) -> dict:
    """Returns empty results (graph backend removed)."""
    return {"query_type": query_type, "results": []}
