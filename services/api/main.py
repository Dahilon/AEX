"""
AEX FastAPI Application — main entry point.

Start with:
    DD_SERVICE=aex DD_ENV=demo ddtrace-run uvicorn services.api.main:app --reload --port 8000
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.market_engine.engine import MarketEngine
from services.graph.service import GraphService
from services.agents.tools import ToolExecutor
from services.agents.market_analyst import MarketAnalystAgent
from services.agents.risk_agent import RiskAgent
from services.observability.metrics import init_datadog, emit_agent_metrics, emit_market_metrics
from services.observability.tracing import init_llm_obs

from .routes import market, shock, analysis, graph, tests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Shared app state (injected into routes via request.app.state) ─────────────

engine = MarketEngine(tick_interval_ms=int(os.environ.get("MARKET_TICK_INTERVAL_MS", 2000)))
graph_service = GraphService()
tool_executor = ToolExecutor(engine, graph_service)
analyst_agent = MarketAnalystAgent(tool_executor)
risk_agent_instance = RiskAgent(tool_executor)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info("Starting AEX services...")

    init_datadog()
    init_llm_obs()

    try:
        graph_service.connect()
        logger.info("Neo4j connected")
    except Exception as e:
        logger.warning(f"Neo4j connection failed (non-fatal): {e}")

    # Register post-tick callbacks
    async def on_market_tick(state):
        snapshot = state.to_snapshot()
        for agent in snapshot["agents"]:
            emit_agent_metrics(agent)
        emit_market_metrics(snapshot)
        await market.broadcast_tick(snapshot)

    engine.on_tick(on_market_tick)
    engine.start()
    logger.info("Market engine started")

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    engine.stop()
    graph_service.close()
    logger.info("AEX shutdown complete")


# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AEX — Agent Exchange API",
    version="0.1.0",
    description="Real-time simulated market for AI agents",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inject shared state into app
app.state.engine = engine
app.state.graph_service = graph_service
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
    }
