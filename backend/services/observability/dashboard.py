"""
Programmatic Datadog Dashboard creation via API.

Creates a comprehensive AEX monitoring dashboard with:
  - Market overview (total cap, cascade probability)
  - Per-agent price timeseries
  - Shock event overlay
  - LLM/Bedrock performance metrics
  - API request latency
  - Engine health
"""

import logging
import os
import threading
from datadog import api

logger = logging.getLogger(__name__)

AGENTS = [
    "fraudguard_v3", "amlscan_pro", "txn_monitor", "complibot_eu",
    "regwatch_us", "sanction_screen", "geointel_live", "threat_mapper",
]

SECTORS = ["FRAUD_AML", "COMPLIANCE", "GEO_OSINT"]


def get_dashboard_definition() -> dict:
    """Return the full dashboard JSON definition."""
    return {
        "title": "AEX — Agent Exchange Live Dashboard",
        "description": "Real-time monitoring for the AEX AI Agent Market simulation. Tracks agent prices, market health, shock impacts, Bedrock LLM usage, and API performance.",
        "layout_type": "ordered",
        "widgets": _build_widgets(),
    }


def create_dashboard() -> dict:
    """
    Create AEX dashboard in Datadog via API.
    Requires both DD_API_KEY and DD_APP_KEY.
    Returns { status, id?, url?, definition? }.
    """
    api_key = (os.environ.get("DD_API_KEY") or "").strip()
    app_key = (os.environ.get("DD_APP_KEY") or "").strip()
    dd_site = os.environ.get("DD_SITE", "datadoghq.com")

    dashboard_def = get_dashboard_definition()

    if not api_key:
        return {"status": "no_api_key", "definition": dashboard_def}

    if not app_key:
        return {
            "status": "no_app_key",
            "message": "Dashboard creation requires DD_APP_KEY. You can import the definition JSON manually at https://app.datadoghq.com/dashboard/lists",
            "definition": dashboard_def,
        }

    try:
        result = api.Dashboard.create(**dashboard_def)
        url = result.get("url", "")
        dash_id = result.get("id", "")
        full_url = f"https://app.{dd_site}{url}" if url else ""
        logger.info("Datadog dashboard created: %s", full_url)
        return {"status": "created", "id": dash_id, "url": full_url}
    except Exception as e:
        logger.error("Failed to create Datadog dashboard: %s", e)
        return {"status": "error", "message": str(e), "definition": dashboard_def}


def _build_widgets() -> list:
    widgets = []

    # ── Row 1: Market Overview ────────────────────────────────────────────────
    widgets.append(_group("Market Overview", [
        _timeseries("Total Market Cap", [
            _query("aex.market.total_cap{service:aex}", "Total Cap")
        ], width=6),
        _timeseries("Cascade Probability", [
            _query("aex.market.cascade_probability{service:aex}", "Cascade %")
        ], width=3),
        _timeseries("Active Shocks", [
            _query("aex.market.active_shocks{service:aex}", "Shocks")
        ], width=3),
    ]))

    # ── Row 2: Agent Prices ───────────────────────────────────────────────────
    price_queries = [
        _query(f"aex.agent.price{{agent_id:{aid},service:aex}}", aid.replace("_", "-"))
        for aid in AGENTS
    ]
    widgets.append(_group("Agent Prices", [
        _timeseries("All Agent Prices", price_queries, width=12),
    ]))

    # ── Row 3: Agent Risk & Volatility ────────────────────────────────────────
    widgets.append(_group("Risk & Volatility", [
        _timeseries("Risk Scores by Agent", [
            _query(f"aex.agent.risk_score{{agent_id:{aid},service:aex}}", aid.replace("_", "-"))
            for aid in AGENTS
        ], width=6),
        _timeseries("Volatility by Agent", [
            _query(f"aex.agent.volatility{{agent_id:{aid},service:aex}}", aid.replace("_", "-"))
            for aid in AGENTS
        ], width=6),
    ]))

    # ── Row 4: Capital Flows ──────────────────────────────────────────────────
    widgets.append(_group("Capital Flows", [
        _timeseries("Inflow Velocity by Agent", [
            _query(f"aex.agent.inflow{{agent_id:{aid},service:aex}}", aid.replace("_", "-"))
            for aid in AGENTS
        ], width=6),
        _timeseries("Market Cap by Agent", [
            _query(f"aex.agent.market_cap{{agent_id:{aid},service:aex}}", aid.replace("_", "-"))
            for aid in AGENTS
        ], width=6),
    ]))

    # ── Row 5: Shock Analysis ─────────────────────────────────────────────────
    widgets.append(_group("Shock Events", [
        _timeseries("Shock Severity", [
            _query("aex.shock.severity{service:aex} by {shock_type}", "Severity")
        ], width=4),
        _timeseries("Shock Count", [
            _query("aex.shock.count{service:aex} by {shock_type}.as_count()", "Count")
        ], width=4),
        _event_timeline(width=4),
    ]))

    # ── Row 6: Bedrock LLM Observability ──────────────────────────────────────
    widgets.append(_group("Bedrock LLM Observability", [
        _timeseries("LLM Latency (ms)", [
            _query("aex.llm.latency_ms{service:aex} by {agent_name}", "Latency")
        ], width=4),
        _timeseries("Token Usage", [
            _query("aex.llm.input_tokens{service:aex} by {agent_name}", "Input"),
            _query("aex.llm.output_tokens{service:aex} by {agent_name}", "Output"),
        ], width=4),
        _timeseries("LLM Calls", [
            _query("aex.llm.calls{service:aex} by {agent_name}.as_count()", "Calls")
        ], width=4),
    ]))

    # ── Row 7: API Performance ────────────────────────────────────────────────
    widgets.append(_group("API Performance", [
        _timeseries("Request Latency (ms)", [
            _query("aex.http.request_latency_ms{service:aex} by {path}", "Latency")
        ], width=4),
        _timeseries("Request Count", [
            _query("aex.http.requests{service:aex} by {path}.as_count()", "Requests")
        ], width=4),
        _timeseries("Engine Tick Latency (ms)", [
            _query("aex.engine.tick_latency_ms{service:aex}", "Tick Time")
        ], width=4),
    ]))

    # ── Row 8: Infrastructure ─────────────────────────────────────────────────
    widgets.append(_group("Infrastructure", [
        _timeseries("WebSocket Connections", [
            _query("aex.ws.connections{service:aex}", "Connections")
        ], width=4),
        _query_value("Current Tick", "aex.market.tick_number{service:aex}", width=2),
        _query_value("Total Market Cap", "aex.market.total_cap{service:aex}", width=3, precision=0),
        _query_value("Cascade Risk %", "aex.market.cascade_probability{service:aex}", width=3),
    ]))

    return widgets


# ── Widget builders ───────────────────────────────────────────────────────────

def _query(q: str, label: str) -> dict:
    return {"query": q, "display_type": "line", "style": {"palette": "dog_classic"}, "metadata": [{"expression": q, "alias_name": label}]}


def _timeseries(title: str, requests: list, width: int = 12) -> dict:
    return {
        "definition": {
            "title": title,
            "type": "timeseries",
            "requests": [{"q": r["query"], "display_type": "line"} for r in requests],
        },
        "layout": {"width": width, "height": 3},
    }


def _query_value(title: str, q: str, width: int = 3, precision: int = 2) -> dict:
    return {
        "definition": {
            "title": title,
            "type": "query_value",
            "requests": [{"q": q, "aggregator": "last"}],
            "precision": precision,
        },
        "layout": {"width": width, "height": 2},
    }


def _event_timeline(width: int = 4) -> dict:
    return {
        "definition": {
            "title": "AEX Events",
            "type": "event_timeline",
            "query": "sources:aex",
        },
        "layout": {"width": width, "height": 3},
    }


def _group(title: str, children: list) -> dict:
    return {
        "definition": {
            "title": title,
            "type": "group",
            "layout_type": "ordered",
            "widgets": children,
        },
    }
