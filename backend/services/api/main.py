"""
AEX FastAPI Application — main entry point.
"""

import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.services.market_engine.engine import MarketEngine
from backend.services.agents.tools import ToolExecutor
from backend.services.agents.market_analyst import MarketAnalystAgent
from backend.services.agents.risk_agent import RiskAgent

from backend.services.observability.datadog_client import init_client
from backend.services.observability.metrics import (
    emit_agent_metrics, emit_market_metrics,
    emit_tick_latency, emit_ws_connections, flush_metrics,
)
from backend.services.observability.tracing import init_llm_obs
from backend.services.observability.events import emit_market_anomaly
from backend.services.observability.middleware import DatadogRequestMetrics
from backend.services.observability.dashboard import create_dashboard
from backend.services.observability.monitors import get_monitor_definitions
from backend.services.observability.correlation import new_run_id

from .routes import market, shock, analysis, graph, tests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = MarketEngine(tick_interval_ms=int(os.environ.get("MARKET_TICK_INTERVAL_MS", 2000)))
tool_executor = ToolExecutor(engine)
analyst_agent = MarketAnalystAgent(tool_executor)
risk_agent_instance = RiskAgent(tool_executor)

_prev_cascade = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _prev_cascade
    logger.info("Starting AEX services...")

    init_client()
    init_llm_obs()

    async def on_market_tick(state):
        global _prev_cascade
        tick_rid = new_run_id("tick")

        snapshot = state.to_snapshot()
        for agent_dict in snapshot["agents"]:
            emit_agent_metrics(agent_dict)
        emit_market_metrics(snapshot)
        emit_ws_connections(len(market.manager.active))
        emit_tick_latency(round(app.state.engine.last_tick_latency_ms, 1))

        cascade = snapshot["cascade_probability"]
        if cascade > 0.5 and _prev_cascade <= 0.5:
            emit_market_anomaly(
                "High Cascade Risk",
                f"Cascade probability crossed 50%: **{cascade:.1%}**\n"
                f"Active shocks: {len(snapshot['active_shocks'])}\n"
                f"Drawdown: {snapshot.get('drawdown_pct', 0):.2f}%",
                severity="error",
            )
        _prev_cascade = cascade

        flush_metrics()
        await market.broadcast_tick(snapshot)

    engine.on_tick(on_market_tick)
    engine.start()
    logger.info("Market engine started")

    yield

    engine.stop()
    logger.info("AEX shutdown complete")


app = FastAPI(
    title="AEX — Agent Exchange API",
    version="0.2.0",
    description="Real-time simulated market for AI agents with Datadog observability",
    lifespan=lifespan,
)

app.add_middleware(DatadogRequestMetrics)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.engine = engine
app.state.analyst_agent = analyst_agent
app.state.risk_agent = risk_agent_instance

app.include_router(market.router,   prefix="/market",   tags=["Market"])
app.include_router(shock.router,    prefix="/shock",    tags=["Shock"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
app.include_router(graph.router,    prefix="/graph",    tags=["Graph"])
app.include_router(tests.router,    prefix="/tests",    tags=["Tests"])


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "tick": engine.state.tick_number,
        "agents": len(engine.state.agents),
        "active_shocks": len(engine.state.active_shocks),
        "ws_connections": len(market.manager.active),
        "drawdown_pct": round(engine.drawdown_pct, 4),
        "peak_market_cap": round(engine.peak_market_cap, 2),
    }


@app.post("/observability/dashboard")
async def create_dd_dashboard():
    result = create_dashboard()
    return result


@app.get("/observability/monitors")
async def get_monitors():
    return {"monitors": get_monitor_definitions()}
