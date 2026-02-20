# Observability (Datadog)

## Philosophy

Observability is not bolted on — it IS the product. The market metrics are the observability. A shock event should be visible in Datadog at the same time it moves prices in the UI. Judges should see a unified story: Shock -> Price Move -> Capital Flow -> Cascade Risk, all traced end-to-end.

---

## Instrumentation Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Auto-instrumentation | `ddtrace` (Python) | Trace all FastAPI requests, HTTP calls |
| Custom metrics | `datadog` Python client / DogStatsD | Market-specific gauges and counters |
| LLM Observability | `ddtrace.llmobs` | Bedrock call tracing (tokens, latency, model) |
| Dashboard | Datadog UI | Pre-built dashboard for demo |

### Setup
```bash
pip install ddtrace datadog
# Run with:
DD_SERVICE=aex DD_ENV=demo ddtrace-run uvicorn services.api.main:app
```

---

## Custom Metrics

### Agent-Level Metrics

| Metric Name | Type | Tags | Description |
|-------------|------|------|-------------|
| `aex.agent.price` | gauge | `agent_id`, `sector` | Current agent price |
| `aex.agent.market_cap` | gauge | `agent_id`, `sector` | Price * total_backing |
| `aex.agent.volatility` | gauge | `agent_id`, `sector` | Rolling 20-tick vol |
| `aex.agent.inflow` | gauge | `agent_id`, `sector` | Net inflow velocity |
| `aex.agent.risk_score` | gauge | `agent_id`, `sector` | Risk score (0-1) |
| `aex.agent.performance_score` | gauge | `agent_id`, `sector` | Performance score (0-1) |
| `aex.agent.price_change_pct` | gauge | `agent_id`, `sector` | Tick-over-tick % change |

### Market-Level Metrics

| Metric Name | Type | Tags | Description |
|-------------|------|------|-------------|
| `aex.market.total_cap` | gauge | — | Sum of all agent market caps |
| `aex.market.cascade_probability` | gauge | — | Cascade risk 0-1 |
| `aex.market.active_shocks` | gauge | — | Number of active (decaying) shocks |
| `aex.market.total_volume` | counter | — | Total buy+sell events this window |

### Shock Metrics

| Metric Name | Type | Tags | Description |
|-------------|------|------|-------------|
| `aex.shock.severity` | gauge | `shock_type`, `sector` | Severity of latest shock |
| `aex.shock.count` | counter | `shock_type` | Total shocks injected |
| `aex.shock.impact_spread` | gauge | `shock_type` | Number of agents impacted |

### Signal Ingestion Metrics

| Metric Name | Type | Tags | Description |
|-------------|------|------|-------------|
| `aex.ingest.signals_received` | counter | `source` | Signals from GDELT/USGS/FX |
| `aex.ingest.latency_ms` | histogram | `source` | Poll-to-process latency |
| `aex.ingest.errors` | counter | `source` | Failed API calls |

---

## Trace Spans

All operations emit distributed trace spans under `DD_SERVICE=aex`.

| Span Name | Parent | Description |
|-----------|--------|-------------|
| `ingest.poll` | root | One polling cycle for a signal source |
| `ingest.normalize` | `ingest.poll` | Normalize raw response to SignalEvent |
| `shock.compute` | root | Convert SignalEvent to ShockEvent |
| `shock.apply` | `shock.compute` | Apply shock to agent fundamentals |
| `market.tick` | root | One market engine tick (all agents) |
| `market.price_update` | `market.tick` | Price calc for one agent |
| `market.graph_sync` | `market.tick` | Push updated state to Neo4j |
| `graph.query` | varies | Execute a Cypher query |
| `agent.analyze` | root | Full Bedrock agent call (tool loop) |
| `agent.tool_call` | `agent.analyze` | One tool execution within agent loop |
| `api.request` | root | FastAPI request (auto by ddtrace) |

### Span Tags (common)
- `agent_id`: which market agent (for agent-specific ops)
- `sector`: sector tag
- `shock_type`: for shock-related spans
- `bedrock.model_id`: for LLM spans

---

## LLM Observability

Using `ddtrace.llmobs` to trace Bedrock calls:

```python
from ddtrace.llmobs import LLMObs

LLMObs.enable(ml_app="aex")

# Wrap Bedrock calls
with LLMObs.llm(
    model_name="anthropic.claude-3-5-sonnet",
    model_provider="bedrock",
    name="market_analyst"
) as span:
    response = bedrock.converse(...)
    LLMObs.annotate(
        span=span,
        input_data=[{"role": "user", "content": prompt}],
        output_data=[{"role": "assistant", "content": response_text}],
        metrics={"input_tokens": usage.inputTokens, "output_tokens": usage.outputTokens}
    )
```

This gives us:
- Token usage per call (input/output)
- Latency per LLM call
- Model name tracking
- Error rate
- Full prompt/response logging (for debug)

---

## Dashboard Specification

### Dashboard Name: "AEX Market Observatory"

#### Row 1: Market Overview (4 widgets)
| Widget | Type | Query |
|--------|------|-------|
| Total Market Cap | Query Value | `avg:aex.market.total_cap{}` |
| Active Shocks | Query Value | `avg:aex.market.active_shocks{}` |
| Cascade Probability | Query Value + conditional (red >0.6) | `avg:aex.market.cascade_probability{}` |
| Total Volume (5m) | Query Value | `sum:aex.market.total_volume{}.as_count()` |

#### Row 2: Agent Prices (1 widget, full width)
| Widget | Type | Query |
|--------|------|-------|
| Agent Price Timeseries | Timeseries | `avg:aex.agent.price{*} by {agent_id}` |

#### Row 3: Shock & Risk (3 widgets)
| Widget | Type | Query |
|--------|------|-------|
| Shock Severity Timeline | Timeseries + events overlay | `avg:aex.shock.severity{*} by {shock_type}` |
| Agent Volatility | Heatmap | `avg:aex.agent.volatility{*} by {agent_id}` |
| Inflow by Sector | Timeseries | `avg:aex.agent.inflow{*} by {sector}` |

#### Row 4: LLM Telemetry (3 widgets)
| Widget | Type | Query |
|--------|------|-------|
| Bedrock Token Usage | Timeseries (stacked) | LLM Obs → tokens by model |
| Bedrock Latency (p50/p95) | Timeseries | `avg:trace.agent.analyze.duration{service:aex}` |
| Bedrock Error Rate | Query Value | `sum:trace.agent.analyze.errors{service:aex}.as_count()` |

#### Row 5: Ingestion Health (3 widgets)
| Widget | Type | Query |
|--------|------|-------|
| Signals Received | Timeseries | `sum:aex.ingest.signals_received{*} by {source}.as_count()` |
| Ingest Latency | Timeseries | `avg:aex.ingest.latency_ms{*} by {source}` |
| Ingest Errors | Timeseries | `sum:aex.ingest.errors{*} by {source}.as_count()` |

---

## What "Good Demo" Looks Like on Datadog

1. **Before shock**: Flat/gentle lines on prices. Low volatility. Cascade probability < 0.2.
2. **Shock injected**: `aex.shock.severity` spikes. Within 2-3 seconds, `aex.agent.price` lines diverge (some up, some down). `aex.agent.volatility` heatmap lights up.
3. **Capital reallocation**: `aex.agent.inflow` shows flows reversing — money leaving risky agents, entering safe havens.
4. **Cascade risk**: `aex.market.cascade_probability` ticks up. If it crosses 0.6, the widget turns red.
5. **Bedrock analysis**: `trace.agent.analyze` span appears. Token usage widget shows the cost. Latency is visible.
6. **Recovery**: Over 30-60 seconds, shock decays. Prices stabilize. Volatility drops. New equilibrium.

The judges see a STORY on the dashboard, not just random metrics.
