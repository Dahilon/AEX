"""
Datadog metric emission for AEX.

All custom metrics follow the pattern: aex.<subsystem>.<name>
Tags: agent_id, sector, shock_type

Usage:
    from services.observability.metrics import emit_agent_metrics, emit_shock_metric
"""

import logging
import os
from datadog import initialize, statsd

logger = logging.getLogger(__name__)

_initialized = False


def init_datadog() -> None:
    global _initialized
    if _initialized:
        return
    initialize(
        api_key=os.environ.get("DD_API_KEY", ""),
        app_key=os.environ.get("DD_APP_KEY", ""),
        statsd_host=os.environ.get("DD_AGENT_HOST", "localhost"),
        statsd_port=int(os.environ.get("DD_AGENT_PORT", 8125)),
    )
    _initialized = True
    logger.info("Datadog initialized")


# ── Agent-level metrics ───────────────────────────────────────────────────────

def emit_agent_metrics(agent_dict: dict) -> None:
    """Emit all per-agent gauges. Call once per agent per tick."""
    tags = [
        f"agent_id:{agent_dict['id']}",
        f"sector:{agent_dict['sector']}",
    ]
    statsd.gauge("aex.agent.price",             agent_dict["price"],             tags=tags)
    statsd.gauge("aex.agent.market_cap",        agent_dict["market_cap"],        tags=tags)
    statsd.gauge("aex.agent.volatility",        agent_dict["volatility"],        tags=tags)
    statsd.gauge("aex.agent.inflow",            agent_dict["inflow_velocity"],   tags=tags)
    statsd.gauge("aex.agent.risk_score",        agent_dict["risk_score"],        tags=tags)
    statsd.gauge("aex.agent.performance_score", agent_dict["performance_score"], tags=tags)
    statsd.gauge("aex.agent.price_change_pct",  agent_dict["price_change_pct"],  tags=tags)


# ── Market-level metrics ──────────────────────────────────────────────────────

def emit_market_metrics(snapshot: dict) -> None:
    """Emit market-wide gauges. Call once per tick."""
    statsd.gauge("aex.market.total_cap",           snapshot["total_market_cap"])
    statsd.gauge("aex.market.cascade_probability", snapshot["cascade_probability"])
    statsd.gauge("aex.market.active_shocks",       len(snapshot["active_shocks"]))


# ── Shock metrics ─────────────────────────────────────────────────────────────

def emit_shock_metric(shock_dict: dict, impacted_agents: int = 0) -> None:
    """Emit shock event metrics when a shock is injected."""
    tags = [
        f"shock_type:{shock_dict['type']}",
    ]
    statsd.gauge("aex.shock.severity",      shock_dict["severity"], tags=tags)
    statsd.increment("aex.shock.count",     tags=tags)
    statsd.gauge("aex.shock.impact_spread", impacted_agents,         tags=tags)


# ── Signal ingestion metrics ──────────────────────────────────────────────────

def emit_ingest_received(source: str) -> None:
    statsd.increment("aex.ingest.signals_received", tags=[f"source:{source}"])


def emit_ingest_latency(source: str, latency_ms: float) -> None:
    statsd.histogram("aex.ingest.latency_ms", latency_ms, tags=[f"source:{source}"])


def emit_ingest_error(source: str) -> None:
    statsd.increment("aex.ingest.errors", tags=[f"source:{source}"])


# ── Volume counter ────────────────────────────────────────────────────────────

def emit_trade_event(action: str, agent_id: str, sector: str) -> None:
    """Call on every buy or sell simulation."""
    tags = [f"action:{action}", f"agent_id:{agent_id}", f"sector:{sector}"]
    statsd.increment("aex.market.total_volume", tags=tags)
