"""
Exportable Datadog Monitor definitions for AEX.

These can be imported via Datadog API (POST /api/v1/monitor)
or pasted into the Datadog UI. They define alerts for:
  1. Cascade probability > 0.6 (market systemic risk)
  2. Bedrock p95 latency > 3000ms (LLM slowness)
  3. Engine tick latency > 200ms (processing bottleneck)
"""


def get_monitor_definitions() -> list[dict]:
    return [
        {
            "name": "[AEX] Cascade Probability > 60%",
            "type": "metric alert",
            "query": "avg(last_5m):avg:aex.market.cascade_probability{service:aex,env:demo} > 0.6",
            "message": (
                "AEX cascade probability is above 60%. "
                "This indicates high systemic risk across the agent market. "
                "Check active shocks and sector correlations.\n\n"
                "@slack-aex-alerts"
            ),
            "tags": ["service:aex", "env:demo", "team:aex"],
            "options": {
                "thresholds": {"critical": 0.6, "warning": 0.4},
                "notify_no_data": False,
                "renotify_interval": 300,
                "evaluation_delay": 60,
            },
        },
        {
            "name": "[AEX] Bedrock LLM Latency > 3s (p95)",
            "type": "metric alert",
            "query": "avg(last_5m):avg:aex.llm.latency_ms{service:aex,env:demo} > 3000",
            "message": (
                "Bedrock LLM latency is above 3 seconds. "
                "This may impact user experience for market analysis. "
                "Check model availability and request patterns.\n\n"
                "@slack-aex-alerts"
            ),
            "tags": ["service:aex", "env:demo", "team:aex"],
            "options": {
                "thresholds": {"critical": 3000, "warning": 2000},
                "notify_no_data": False,
                "renotify_interval": 300,
            },
        },
        {
            "name": "[AEX] Engine Tick Latency > 200ms",
            "type": "metric alert",
            "query": "avg(last_5m):avg:aex.engine.tick_latency_ms{service:aex,env:demo} > 200",
            "message": (
                "Market engine tick processing is taking over 200ms. "
                "This could cause delayed price updates. "
                "The tick interval is 2000ms so this is 10% of budget.\n\n"
                "@slack-aex-alerts"
            ),
            "tags": ["service:aex", "env:demo", "team:aex"],
            "options": {
                "thresholds": {"critical": 200, "warning": 100},
                "notify_no_data": False,
                "renotify_interval": 300,
            },
        },
    ]
