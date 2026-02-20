"""
Datadog metric emission for AEX.

All custom metrics follow the pattern: aex.<subsystem>.<name>
Tags: agent_id, sector, shock_type, model, agent_name

Uses DatadogClient for HTTP submission. Batches all per-tick metrics
into a single API call via flush_metrics().
"""

import logging
import time
import threading

from .datadog_client import get_client
from .correlation import run_id_tags

logger = logging.getLogger(__name__)

_metric_buffer: list[dict] = []
_buffer_lock = threading.Lock()
_counter_state: dict[str, float] = {}

# Drawdown tracking
_peak_market_cap: float = 0.0
_drawdown_pct: float = 0.0

# ── LLM cost model ───────────────────────────────────────────────────────────
# Claude 3.5 Sonnet via Bedrock: $3/M input, $15/M output (as of 2025-Q4).
# These are approximate for demo/hackathon purposes.
_COST_PER_INPUT_TOKEN = 3.0 / 1_000_000
_COST_PER_OUTPUT_TOKEN = 15.0 / 1_000_000


def _now() -> float:
    return time.time()


def _buffer(metric: str, value: float, mtype: str = "gauge",
            tags: list[str] | None = None) -> None:
    with _buffer_lock:
        _metric_buffer.append({
            "metric": metric,
            "points": [(_now(), value)],
            "type": mtype,
            "tags": (tags or []) + run_id_tags(),
        })


def flush_metrics() -> None:
    """Send all buffered metrics in one HTTP call. Call once per tick."""
    with _buffer_lock:
        if not _metric_buffer:
            return
        batch = _metric_buffer.copy()
        _metric_buffer.clear()
    get_client().submit_metrics(batch)


# ── Convenience wrappers ──────────────────────────────────────────────────────

def _gauge(m: str, v: float, tags: list[str] | None = None) -> None:
    _buffer(m, v, "gauge", tags)

def _count(m: str, tags: list[str] | None = None) -> None:
    all_tags = (tags or []) + run_id_tags()
    key = f"{m}|{'|'.join(sorted(all_tags))}"
    _counter_state[key] = _counter_state.get(key, 0) + 1
    _buffer(m, _counter_state[key], "count", tags)


# ── Agent-level metrics ───────────────────────────────────────────────────────

def emit_agent_metrics(agent_dict: dict) -> None:
    tags = [f"agent_id:{agent_dict['id']}", f"sector:{agent_dict['sector']}"]
    _gauge("aex.agent.price",             agent_dict["price"],             tags=tags)
    _gauge("aex.agent.market_cap",        agent_dict["market_cap"],        tags=tags)
    _gauge("aex.agent.volatility",        agent_dict["volatility"],        tags=tags)
    _gauge("aex.agent.inflow",            agent_dict["inflow_velocity"],   tags=tags)
    _gauge("aex.agent.risk_score",        agent_dict["risk_score"],        tags=tags)
    _gauge("aex.agent.performance_score", agent_dict["performance_score"], tags=tags)
    _gauge("aex.agent.price_change_pct",  agent_dict["price_change_pct"],  tags=tags)


# ── Market-level metrics ──────────────────────────────────────────────────────

def emit_market_metrics(snapshot: dict) -> None:
    global _peak_market_cap, _drawdown_pct

    cap = snapshot["total_market_cap"]
    _gauge("aex.market.total_cap",           cap)
    _gauge("aex.market.cascade_probability", snapshot["cascade_probability"])
    _gauge("aex.market.active_shocks",       len(snapshot["active_shocks"]))
    _gauge("aex.market.tick_number",         snapshot["tick_number"])

    if cap > _peak_market_cap:
        _peak_market_cap = cap
    if _peak_market_cap > 0:
        _drawdown_pct = ((cap - _peak_market_cap) / _peak_market_cap) * 100
    _gauge("aex.market.drawdown_pct", round(_drawdown_pct, 4))
    _gauge("aex.market.peak_cap",     round(_peak_market_cap, 2))


# ── Shock metrics ─────────────────────────────────────────────────────────────

def emit_shock_metric(shock_dict: dict, impacted_agents: int = 0) -> None:
    tags = [f"shock_type:{shock_dict['type']}"]
    _gauge("aex.shock.severity",      shock_dict["severity"], tags=tags)
    _count("aex.shock.count",         tags=tags)
    _gauge("aex.shock.impact_spread", impacted_agents,        tags=tags)


# ── LLM / Bedrock metrics ────────────────────────────────────────────────────

def estimate_llm_cost(input_tokens: int, output_tokens: int) -> float:
    return round(
        input_tokens * _COST_PER_INPUT_TOKEN + output_tokens * _COST_PER_OUTPUT_TOKEN,
        6,
    )


def emit_llm_metrics(agent_name: str, model: str, input_tokens: int,
                     output_tokens: int, latency_ms: float) -> None:
    tags = [f"agent_name:{agent_name}", f"model:{model}"]
    _gauge("aex.llm.input_tokens",        input_tokens,  tags=tags)
    _gauge("aex.llm.output_tokens",       output_tokens, tags=tags)
    _gauge("aex.llm.total_tokens",        input_tokens + output_tokens, tags=tags)
    _gauge("aex.llm.latency_ms",          latency_ms,    tags=tags)
    _gauge("aex.llm.cost_estimate_usd",   estimate_llm_cost(input_tokens, output_tokens), tags=tags)
    _count("aex.llm.calls",               tags=tags)
    flush_metrics()


# ── Engine health metrics ─────────────────────────────────────────────────────

def emit_tick_latency(latency_ms: float) -> None:
    _gauge("aex.engine.tick_latency_ms", latency_ms)

def emit_ws_connections(count: int) -> None:
    _gauge("aex.ws.connections", count)


# ── HTTP request metrics ──────────────────────────────────────────────────────

def emit_request_metrics(method: str, path: str, status_code: int,
                         latency_ms: float) -> None:
    tags = [f"method:{method}", f"path:{path}", f"status:{status_code}"]
    _gauge("aex.http.request_latency_ms", latency_ms, tags=tags)
    _count("aex.http.requests",           tags=tags)
    if status_code >= 400:
        _count("aex.http.errors", tags=tags)
    flush_metrics()


# ── Test metrics ──────────────────────────────────────────────────────────────

def emit_test_metrics(test_name: str, passed: bool, duration_ms: float) -> None:
    tags = [f"test_name:{test_name}", f"result:{'pass' if passed else 'fail'}"]
    _gauge("aex.test.duration_ms", duration_ms, tags=tags)
    _count("aex.test.runs",        tags=tags)
    flush_metrics()
