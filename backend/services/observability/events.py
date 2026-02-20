"""
Datadog Events API integration.

Sends rich events to the Datadog event stream for shocks, analysis runs,
and risk level changes. Events show up in dashboards and can trigger alerts.
"""

import logging
import os
import threading
import time
from datadog import api

logger = logging.getLogger(__name__)


def _post_event(title: str, text: str, tags: list[str],
                alert_type: str = "info", source: str = "aex") -> None:
    """Fire-and-forget event submission."""
    api_key = (os.environ.get("DD_API_KEY") or "").strip()
    if not api_key:
        return

    def _send():
        try:
            api.Event.create(
                title=title,
                text=text,
                tags=["service:aex", "env:demo"] + tags,
                alert_type=alert_type,
                source_type_name=source,
            )
        except Exception as e:
            logger.debug("Datadog event send failed: %s", e)
    threading.Thread(target=_send, daemon=True).start()


def emit_shock_event(shock_dict: dict, agent_count: int = 0) -> None:
    """Post a Datadog event when a market shock is injected."""
    shock_type = shock_dict.get("type", "UNKNOWN")
    severity = shock_dict.get("severity", 0)
    desc = shock_dict.get("description", "")

    alert = "warning" if severity < 0.5 else "error"
    title = f"AEX Shock: {shock_type} (severity {severity:.0%})"
    text = (
        f"**Shock Type:** {shock_type}\n"
        f"**Severity:** {severity:.2f}\n"
        f"**Description:** {desc}\n"
        f"**Impacted Agents:** {agent_count}\n"
        f"**Source:** {shock_dict.get('source', 'manual')}\n\n"
        f"Shock will decay over 4 ticks with schedule: 100% → 60% → 30% → 10%"
    )
    _post_event(title, text, [f"shock_type:{shock_type}"], alert_type=alert)


def emit_analysis_event(agent_name: str, result: dict) -> None:
    """Post a Datadog event when Bedrock analysis completes."""
    model = result.get("model", "unknown")
    latency = result.get("latency_ms", 0)
    tokens_in = result.get("input_tokens", 0)
    tokens_out = result.get("output_tokens", 0)
    cached = result.get("cached", False)
    analysis_text = result.get("text", "")[:500]

    title = f"AEX Bedrock Analysis: {agent_name}" + (" (cached)" if cached else "")
    text = (
        f"**Model:** {model}\n"
        f"**Latency:** {latency}ms\n"
        f"**Tokens:** {tokens_in} in / {tokens_out} out\n"
        f"**Cached:** {cached}\n\n"
        f"---\n\n{analysis_text}"
    )
    _post_event(title, text, [f"agent_name:{agent_name}", f"model:{model}"], alert_type="info")


def emit_risk_event(result: dict) -> None:
    """Post a Datadog event when risk assessment completes, especially for HIGH/CRITICAL."""
    risk_level = result.get("risk_level", "MEDIUM")
    text_preview = result.get("text", "")[:500]

    alert_map = {"LOW": "info", "MEDIUM": "warning", "HIGH": "error", "CRITICAL": "error"}
    alert = alert_map.get(risk_level, "warning")

    title = f"AEX Risk Assessment: {risk_level}"
    text = (
        f"**Risk Level:** {risk_level}\n"
        f"**Model:** {result.get('model', 'unknown')}\n"
        f"**Latency:** {result.get('latency_ms', 0)}ms\n\n"
        f"---\n\n{text_preview}"
    )
    _post_event(title, text, [f"risk_level:{risk_level}"], alert_type=alert)


def emit_market_anomaly(anomaly_type: str, details: str, severity: str = "warning") -> None:
    """Post an event for detected market anomalies (cascade risk, flash crash, etc.)."""
    title = f"AEX Market Anomaly: {anomaly_type}"
    _post_event(title, details, [f"anomaly_type:{anomaly_type}"], alert_type=severity)
