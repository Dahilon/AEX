"""
AEX FastAPI Application — main entry point.

Start with:
    DD_SERVICE=aex DD_ENV=demo ddtrace-run uvicorn backend.services.api.main:app --reload --port 8000
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
from backend.services.observability.metrics import (
    init_datadog, emit_agent_metrics, emit_market_metrics,
    emit_tick_latency, emit_ws_connections, flush_metrics,
)
from backend.services.observability.tracing import init_llm_obs
from backend.services.observability.events import emit_market_anomaly
from backend.services.observability.middleware import DatadogRequestMetrics
from backend.services.observability.dashboard import create_dashboard

from .routes import market, shock, analysis, graph, tests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Shared app state (injected into routes via request.app.state) ─────────────

engine = MarketEngine(tick_interval_ms=int(os.environ.get("MARKET_TICK_INTERVAL_MS", 2000)))
tool_executor = ToolExecutor(engine)
analyst_agent = MarketAnalystAgent(tool_executor)
risk_agent_instance = RiskAgent(tool_executor)

_prev_cascade = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _prev_cascade
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info("Starting AEX services...")

    init_datadog()
    init_llm_obs()

    async def on_market_tick(state):
        global _prev_cascade
        tick_start = time.time()

        snapshot = state.to_snapshot()
        for agent in snapshot["agents"]:
            emit_agent_metrics(agent)
        emit_market_metrics(snapshot)

        emit_ws_connections(len(market.manager.active))

        cascade = snapshot["cascade_probability"]
        if cascade > 0.5 and _prev_cascade <= 0.5:
            emit_market_anomaly(
                "High Cascade Risk",
                f"Cascade probability crossed 50% threshold: **{cascade:.1%}**\n"
                f"Active shocks: {len(snapshot['active_shocks'])}",
                severity="error",
            )
        _prev_cascade = cascade

        tick_ms = (time.time() - tick_start) * 1000
        emit_tick_latency(round(tick_ms, 1))

        flush_metrics()

        await market.broadcast_tick(snapshot)

    engine.on_tick(on_market_tick)
    engine.start()
    logger.info("Market engine started")

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    engine.stop()
    logger.info("AEX shutdown complete")


# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AEX — Agent Exchange API",
    version="0.1.0",
    description="Real-time simulated market for AI agents",
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

# Inject shared state into app
app.state.engine = engine
app.state.analyst_agent = analyst_agent
app.state.risk_agent = risk_agent_instance

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(market.router,   prefix="/market",   tags=["Market"])
app.include_router(shock.router,    prefix="/shock",    tags=["Shock"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
app.include_router(graph.router,    prefix="/graph",    tags=["Graph"])
app.include_router(tests.router,    prefix="/tests",    tags=["Tests"])


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "tick": app.state.engine.state.tick_number,
        "agents": len(app.state.engine.state.agents),
        "active_shocks": len(app.state.engine.state.active_shocks),
        "ws_connections": len(market.manager.active),
    }


@app.post("/observability/dashboard")
async def create_dd_dashboard():
    """Create or recreate the AEX Datadog dashboard via API."""
    result = create_dashboard()
    if result:
        return {"status": "created", **result}
    return {"status": "failed", "message": "Could not create dashboard. Check DD_API_KEY."}
