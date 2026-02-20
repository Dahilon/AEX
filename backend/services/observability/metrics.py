"""
Datadog metric emission for AEX.

All custom metrics follow the pattern: aex.<subsystem>.<name>
Tags: agent_id, sector, shock_type

Supports two modes:
  1. DogStatsD (when DD_AGENT_HOST is set — local Datadog agent running)
  2. HTTP API  (when only DD_API_KEY is set — agentless, sends directly to Datadog)

HTTP mode batches all per-tick metrics into a single API call for efficiency.
"""

import logging
import os
import time
import threading
from datadog import initialize, statsd, api

logger = logging.getLogger(__name__)

_initialized = False
_datadog_enabled = False
_use_http_api = False
_dd_tags_base: list[str] = []
_counter_state: dict[str, float] = {}

_metric_buffer: list[dict] = []
_buffer_lock = threading.Lock()


def init_datadog() -> None:
    global _initialized, _datadog_enabled, _use_http_api, _dd_tags_base
    if _initialized:
        return
    api_key = (os.environ.get("DD_API_KEY") or "").strip()
    if not api_key:
        _datadog_enabled = False
        _initialized = True
        logger.info("Datadog disabled (DD_API_KEY not set)")
        return

    dd_site = os.environ.get("DD_SITE", "datadoghq.com")
    service = os.environ.get("DD_SERVICE", "aex")
    env = os.environ.get("DD_ENV", "demo")
    _dd_tags_base = [f"service:{service}", f"env:{env}"]

    agent_host = (os.environ.get("DD_AGENT_HOST") or "").strip()
    if agent_host:
        initialize(
            api_key=api_key,
            app_key=os.environ.get("DD_APP_KEY", ""),
            statsd_host=agent_host,
            statsd_port=int(os.environ.get("DD_AGENT_PORT", 8125)),
        )
        _use_http_api = False
        _datadog_enabled = True
        _initialized = True
        logger.info("Datadog initialized via DogStatsD → %s", agent_host)
        return

    initialize(
        api_key=api_key,
        app_key=os.environ.get("DD_APP_KEY", ""),
        api_host=f"https://api.{dd_site}",
    )
    _use_http_api = True
    _datadog_enabled = True
    _initialized = True
    logger.info("Datadog initialized via HTTP API → %s (agentless)", dd_site)


# ── Batched HTTP submission ───────────────────────────────────────────────────

def _buffer_metric(metric: str, value: float, metric_type: str = "gauge",
                   tags: list[str] | None = None) -> None:
    """Add a metric to the buffer. Call flush_metrics() to send."""
    all_tags = _dd_tags_base + (tags or [])
    with _buffer_lock:
        _metric_buffer.append({
            "metric": metric,
            "points": [(time.time(), value)],
            "type": metric_type,
            "tags": all_tags,
        })


def flush_metrics() -> None:
    """Send all buffered metrics in one HTTP call. Call once per tick."""
    if not _datadog_enabled or not _use_http_api:
        return
    with _buffer_lock:
        if not _metric_buffer:
            return
        batch = _metric_buffer.copy()
        _metric_buffer.clear()

    def _post():
        try:
            api.Metric.send(batch)
        except Exception as e:
            logger.debug("Datadog batch metric send failed: %s", e)
    threading.Thread(target=_post, daemon=True).start()


def _send_single_http(series: list[dict]) -> None:
    """Fire-and-forget single metric submission (for low-frequency events)."""
    def _post():
        try:
            api.Metric.send(series)
        except Exception as e:
            logger.debug("Datadog HTTP metric send failed: %s", e)
    threading.Thread(target=_post, daemon=True).start()


def _gauge(metric: str, value: float, tags: list[str] | None = None) -> None:
    if not _datadog_enabled:
        return
    if _use_http_api:
        _buffer_metric(metric, value, "gauge", tags)
    else:
        statsd.gauge(metric, value, tags=_dd_tags_base + (tags or []))


def _increment(metric: str, tags: list[str] | None = None) -> None:
    if not _datadog_enabled:
        return
    all_tags = _dd_tags_base + (tags or [])
    if _use_http_api:
        key = f"{metric}|{'|'.join(sorted(all_tags))}"
        _counter_state[key] = _counter_state.get(key, 0) + 1
        _buffer_metric(metric, _counter_state[key], "count", tags)
    else:
        statsd.increment(metric, tags=all_tags)


def _histogram(metric: str, value: float, tags: list[str] | None = None) -> None:
    if not _datadog_enabled:
        return
    if _use_http_api:
        _buffer_metric(metric, value, "gauge", tags)
    else:
        statsd.histogram(metric, value, tags=_dd_tags_base + (tags or []))


# ── Agent-level metrics ───────────────────────────────────────────────────────

def emit_agent_metrics(agent_dict: dict) -> None:
    """Emit all per-agent gauges. Call once per agent per tick."""
    if not _datadog_enabled:
        return
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
    """Emit market-wide gauges. Call once per tick."""
    if not _datadog_enabled:
        return
    _gauge("aex.market.total_cap",           snapshot["total_market_cap"])
    _gauge("aex.market.cascade_probability", snapshot["cascade_probability"])
    _gauge("aex.market.active_shocks",       len(snapshot["active_shocks"]))
    _gauge("aex.market.tick_number",         snapshot["tick_number"])


# ── Shock metrics ─────────────────────────────────────────────────────────────

def emit_shock_metric(shock_dict: dict, impacted_agents: int = 0) -> None:
    """Emit shock event metrics when a shock is injected."""
    if not _datadog_enabled:
        return
    tags = [f"shock_type:{shock_dict['type']}"]
    _gauge("aex.shock.severity",      shock_dict["severity"], tags=tags)
    _increment("aex.shock.count",     tags=tags)
    _gauge("aex.shock.impact_spread", impacted_agents,        tags=tags)


# ── LLM / Bedrock metrics ────────────────────────────────────────────────────

def emit_llm_metrics(agent_name: str, model: str, input_tokens: int,
                     output_tokens: int, latency_ms: float) -> None:
    """Emit LLM call metrics for Datadog dashboards."""
    if not _datadog_enabled:
        return
    tags = [f"agent_name:{agent_name}", f"model:{model}"]
    _gauge("aex.llm.input_tokens",  input_tokens,  tags=tags)
    _gauge("aex.llm.output_tokens", output_tokens,  tags=tags)
    _gauge("aex.llm.total_tokens",  input_tokens + output_tokens, tags=tags)
    _gauge("aex.llm.latency_ms",    latency_ms,     tags=tags)
    _increment("aex.llm.calls",     tags=tags)
    if _use_http_api:
        flush_metrics()


# ── Engine health metrics ─────────────────────────────────────────────────────

def emit_tick_latency(latency_ms: float) -> None:
    """Track how long each market engine tick takes to process."""
    if not _datadog_enabled:
        return
    _gauge("aex.engine.tick_latency_ms", latency_ms)


def emit_ws_connections(count: int) -> None:
    """Track number of active WebSocket connections."""
    if not _datadog_enabled:
        return
    _gauge("aex.ws.connections", count)


# ── HTTP request metrics (FastAPI middleware) ─────────────────────────────────

def emit_request_metrics(method: str, path: str, status_code: int,
                         latency_ms: float) -> None:
    """Emit per-request metrics like APM traces."""
    if not _datadog_enabled:
        return
    tags = [f"method:{method}", f"path:{path}", f"status:{status_code}"]
    _gauge("aex.http.request_latency_ms", latency_ms, tags=tags)
    _increment("aex.http.requests",       tags=tags)
    if status_code >= 400:
        _increment("aex.http.errors", tags=tags)
    if _use_http_api:
        flush_metrics()


# ── Signal ingestion metrics ──────────────────────────────────────────────────

def emit_ingest_received(source: str) -> None:
    if not _datadog_enabled:
        return
    _increment("aex.ingest.signals_received", tags=[f"source:{source}"])


def emit_ingest_latency(source: str, latency_ms: float) -> None:
    if not _datadog_enabled:
        return
    _histogram("aex.ingest.latency_ms", latency_ms, tags=[f"source:{source}"])


def emit_ingest_error(source: str) -> None:
    if not _datadog_enabled:
        return
    _increment("aex.ingest.errors", tags=[f"source:{source}"])


# ── Volume counter ────────────────────────────────────────────────────────────

def emit_trade_event(action: str, agent_id: str, sector: str) -> None:
    """Call on every buy or sell simulation."""
    if not _datadog_enabled:
        return
    _increment("aex.market.total_volume", tags=[f"action:{action}", f"agent_id:{agent_id}", f"sector:{sector}"])
