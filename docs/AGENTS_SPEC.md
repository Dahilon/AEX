# Bedrock Agents Specification

## Overview

AEX uses Amazon Bedrock's Converse API to power two specialized agents. Both agents use tool-use (function calling) to access market data and graph insights. They do NOT have access to real financial data and must never hallucinate real-world financial advice.

**Model**: `anthropic.claude-3-5-sonnet-20241022-v2:0` (or `amazon.nova-pro-v1:0` as fallback)
**Region**: `us-east-1`
**API**: `bedrock-runtime` Converse API with toolConfig

---

## Agent 1: Market Analyst

### Purpose
Explain why agent prices moved, tie movements to shocks and metrics, predict short-horizon direction, and recommend allocations.

### System Prompt
```
You are the AEX Market Analyst — an AI agent that analyzes a simulated market of AI agents.

CRITICAL RULES:
- This is a SIMULATION. All prices, agents, and capital flows are simulated.
- NEVER reference real stocks, real companies, or real financial instruments.
- NEVER give real financial advice. Always clarify this is a simulation.
- Base ALL analysis on data from your tools. Do not hallucinate metrics.

YOUR JOB:
1. Explain price movements by correlating with shock events and metric changes.
2. Identify top movers and the reasons behind their moves.
3. Predict short-term direction (next 1-3 ticks) based on current trends.
4. Suggest allocation adjustments (which agents to overweight/underweight).

FORMAT:
- Lead with a 1-sentence summary.
- Use bullet points for key findings.
- End with a "Recommended Action" section.
- Always cite which metric or shock drove your conclusion.
```

### Tools Available

#### tool: market_snapshot
```json
{
  "name": "market_snapshot",
  "description": "Returns current market state: all agent prices, fundamentals, sector averages, and recent shock events.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "include_history": {
        "type": "boolean",
        "description": "If true, include last 20 price ticks per agent"
      },
      "sector_filter": {
        "type": "string",
        "description": "Optional: filter to a specific sector",
        "enum": ["FRAUD_AML", "COMPLIANCE", "GEO_OSINT"]
      }
    },
    "required": []
  }
}
```

**Response schema**:
```json
{
  "timestamp": "ISO8601",
  "total_market_cap": 50000.0,
  "agents": [
    {
      "id": "fraudguard_v3",
      "name": "FraudGuard-v3",
      "sector": "FRAUD_AML",
      "price": 142.50,
      "price_change_pct": -3.2,
      "market_cap": 7125.0,
      "usage_score": 0.85,
      "performance_score": 0.78,
      "risk_score": 0.35,
      "volatility": 0.045,
      "inflow_velocity": -0.12
    }
  ],
  "sectors": [
    {
      "id": "FRAUD_AML",
      "avg_price_change_pct": -2.8,
      "total_market_cap": 15800.0
    }
  ],
  "recent_shocks": [
    {
      "type": "REGULATION",
      "severity": 0.7,
      "timestamp": "ISO8601",
      "description": "EU AI Act enforcement announcement"
    }
  ]
}
```

#### tool: graph_query
```json
{
  "name": "graph_query",
  "description": "Query the capital flow graph. Returns subgraph data about capital flows, concentration, and contagion paths.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query_type": {
        "type": "string",
        "description": "Type of graph query to run",
        "enum": ["top_inflow", "concentration_risk", "contagion_path", "cross_sector_exposure", "most_impacted_users"]
      },
      "params": {
        "type": "object",
        "description": "Query-specific parameters (e.g., shock_id for contagion_path)",
        "properties": {
          "shock_id": { "type": "string" },
          "agent_id": { "type": "string" },
          "limit": { "type": "integer" }
        }
      }
    },
    "required": ["query_type"]
  }
}
```

**Response schema** (varies by query_type, example for `top_inflow`):
```json
{
  "query_type": "top_inflow",
  "results": [
    {
      "agent": "CompliBot-EU",
      "sector": "COMPLIANCE",
      "total_inflow": 12500.0,
      "pool_count": 7,
      "price": 210.0
    }
  ]
}
```

---

## Agent 2: Risk Agent

### Purpose
Detect bubbles, manipulation patterns, concentration risk, and cascade probability. Acts as a "market surveillance" system.

### System Prompt
```
You are the AEX Risk Agent — a market surveillance AI for the AEX agent market simulation.

CRITICAL RULES:
- This is a SIMULATION. All data is simulated.
- NEVER reference real financial markets or instruments.
- Be conservative: flag risks early, explain clearly.

YOUR JOB:
1. Detect concentration risk (single pool dominates an agent's backing).
2. Identify potential manipulation patterns (wash trading, pump-and-dump).
3. Calculate cascade probability (if one agent crashes, how many follow?).
4. Flag bubble conditions (price disconnected from fundamentals).

FORMAT:
- Lead with RISK LEVEL: LOW / MEDIUM / HIGH / CRITICAL.
- List each risk finding as: [RISK TYPE] Description + Evidence.
- End with "Cascade Assessment" — probability and which agents are most at risk.
- Always cite specific metrics (HHI values, inflow numbers, price/fundamental gaps).
```

### Tools Available

Same two tools: `market_snapshot` and `graph_query` (same schemas as above).

### Risk Detection Logic (guidance for the agent)

The Risk Agent should look for:

| Risk Type | Signal | Metric to Check |
|-----------|--------|-----------------|
| Concentration | Single pool > 40% of agent's backing | graph_query("concentration_risk") |
| Wash Trading | Same-direction trades from few users | graph_query("top_inflow") anomalies |
| Bubble | Price up > 30% but fundamentals flat | market_snapshot → compare price_change vs performance_score |
| Cascade | Multiple agents correlated via shared pools | graph_query("cross_sector_exposure") |

---

## Guardrails

### Input Guardrails
- Max 1 tool call per agent turn (to limit latency)
- Timeout: 15 seconds per Bedrock call
- If tool returns error, agent must say "Unable to retrieve data" not hallucinate

### Output Guardrails
- Response must be < 500 tokens
- Must contain the word "simulation" or "simulated" at least once
- Must NOT contain: specific real company names, real stock tickers, "buy" or "sell" as financial advice
- If output fails guardrails, truncate and append: "[This analysis is for a simulated market only]"

### Fallback Behavior
- If Bedrock returns error → return cached last analysis + "[Cached analysis - live update unavailable]"
- If Bedrock latency > 15s → cancel, return cached + "[Timeout - showing cached analysis]"
- Cache last successful analysis per agent type (Market Analyst / Risk Agent)

---

## Integration Pattern

```
User clicks "Run Analysis"
    │
    ▼
FastAPI endpoint: POST /analysis/run
    │
    ├── Call market_engine.get_snapshot()      → market data
    ├── Call graph_service.run_query()         → graph data
    │
    ▼
Construct Bedrock Converse request:
    - system prompt (per agent type)
    - user message: "Analyze the current market state"
    - toolConfig: [market_snapshot, graph_query]
    │
    ▼
bedrock_runtime.converse(modelId, messages, toolConfig)
    │
    ├── If tool_use in response → execute tool → send result back → get final response
    │
    ▼
Return analysis text to UI
    │
    ▼
Emit Datadog span: agent.analyze (duration, tokens, model)
Emit Datadog LLM Observability event
```
