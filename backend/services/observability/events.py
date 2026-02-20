"""
Datadog Events API integration.

Sends rich events to the Datadog event stream for shocks, analysis runs,
risk level changes, anomalies, and test results.
All events include run_id for correlation.
"""

import logging
from .datadog_client import get_client
from .correlation import get_run_id

logger = logging.getLogger(__name__)


def _run_tag() -> list[str]:
    rid = get_run_id()
    return [f"run_id:{rid}"] if rid else []


def emit_shock_event(shock_dict: dict, agent_count: int = 0) -> None:
    shock_type = shock_dict.get("type", "UNKNOWN")
    severity = shock_dict.get("severity", 0)
    desc = shock_dict.get("description", "")
    run_id = get_run_id()

    alert = "warning" if severity < 0.5 else "error"
    title = f"AEX Shock: {shock_type} (severity {severity:.0%})"
    text = (
        f"**Shock Type:** {shock_type}\n"
        f"**Severity:** {severity:.2f}\n"
        f"**Description:** {desc}\n"
        f"**Impacted Agents:** {agent_count}\n"
        f"**Source:** {shock_dict.get('source', 'manual')}\n"
        f"**run_id:** `{run_id}`\n\n"
        f"Shock decays over 4 ticks: 100% → 60% → 30% → 10%"
    )
    get_client().submit_event(
        title, text,
        [f"shock_type:{shock_type}"] + _run_tag(),
        alert_type=alert,
    )


def emit_analysis_event(agent_name: str, result: dict) -> None:
    model = result.get("model", "unknown")
    latency = result.get("latency_ms", 0)
    tokens_in = result.get("input_tokens", 0)
    tokens_out = result.get("output_tokens", 0)
    cost = result.get("cost_estimate_usd", 0)
    cached = result.get("cached", False)
    run_id = get_run_id()

    title = f"AEX Bedrock: {agent_name}" + (" (cached)" if cached else "")
    text = (
        f"**Model:** {model}\n"
        f"**Latency:** {latency}ms\n"
        f"**Tokens:** {tokens_in} in / {tokens_out} out\n"
        f"**Est. Cost:** ${cost:.6f}\n"
        f"**run_id:** `{run_id}`\n\n"
        f"---\n\n{result.get('text', '')[:500]}"
    )
    get_client().submit_event(
        title, text,
        [f"agent_name:{agent_name}", f"model:{model}"] + _run_tag(),
        alert_type="info",
    )


def emit_risk_event(result: dict) -> None:
    risk_level = result.get("risk_level", "MEDIUM")
    run_id = get_run_id()

    alert_map = {"LOW": "info", "MEDIUM": "warning", "HIGH": "error", "CRITICAL": "error"}
    title = f"AEX Risk: {risk_level}"
    text = (
        f"**Risk Level:** {risk_level}\n"
        f"**Model:** {result.get('model', 'unknown')}\n"
        f"**Latency:** {result.get('latency_ms', 0)}ms\n"
        f"**run_id:** `{run_id}`\n\n"
        f"---\n\n{result.get('text', '')[:500]}"
    )
    get_client().submit_event(
        title, text,
        [f"risk_level:{risk_level}"] + _run_tag(),
        alert_type=alert_map.get(risk_level, "warning"),
    )


def emit_market_anomaly(anomaly_type: str, details: str,
                        severity: str = "warning") -> None:
    title = f"AEX Anomaly: {anomaly_type}"
    get_client().submit_event(
        title, details,
        [f"anomaly_type:{anomaly_type}"] + _run_tag(),
        alert_type=severity,
    )


def emit_test_event(summary: str, results: list[dict], run_id: str) -> None:
    passed = sum(1 for r in results if r.get("status") == "PASS")
    total = len(results)
    alert = "success" if passed == total else "warning"

    details_lines = []
    for r in results:
        icon = "✅" if r["status"] == "PASS" else "❌"
        details_lines.append(f"{icon} **{r['test_name']}**: {r['status']} ({r.get('duration_ms', 0)}ms)")

    text = (
        f"**Summary:** {summary}\n"
        f"**run_id:** `{run_id}`\n\n"
        + "\n".join(details_lines)
    )
    get_client().submit_event(
        f"AEX Tests: {summary}", text,
        [f"run_id:{run_id}"],
        alert_type=alert,
    )
