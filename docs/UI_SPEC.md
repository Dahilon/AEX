# UI Specification (CopilotKit)

## Overview

Single-page Operator Console built with Next.js + CopilotKit. The page shows the market, lets operators inject shocks, run analysis, view the graph, and chat with the AI analyst.

**Framework**: Next.js 14 (App Router)
**UI Library**: CopilotKit (`@copilotkit/react-ui`, `@copilotkit/react-core`)
**Styling**: Tailwind CSS
**Charts**: Lightweight charting (recharts or lightweight-charts)
**Graph**: Neovis.js (embedded Neo4j visualization) or link to Neo4j Browser

---

## Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  HEADER: "AEX - Agent Exchange"    Total Mkt Cap: $XX,XXX      │
│  [Inject Shock ▼]  [Run Analysis]  [Run Tests]  [Graph View]   │
├──────────────────────────────────────────┬──────────────────────┤
│                                          │                      │
│         AGENT MARKET TABLE               │   COPILOTKIT CHAT    │
│                                          │                      │
│  Agent     | Price | 24h  | Vol | MCap  │   "Why did CompliBot │
│  ──────────┼───────┼──────┼─────┼────── │    spike?"           │
│  FraudGrd  | $138  | -3.2%| 0.04| $6.9K │                      │
│  AMLScan   | $95   | -2.1%| 0.03| $4.7K │   > CompliBot-EU saw│
│  CompliBot | $224  | +6.7%| 0.06| $11.2K│   a 6.7% price      │
│  RegWatch  | $171  | +3.4%| 0.04| $8.5K │   increase driven by │
│  ...       |       |      |     |       │   the REGULATION     │
│                                          │   shock (severity    │
│  ────────────────────────────────────── │   0.7)...            │
│                                          │                      │
│         MINI PRICE CHART                 │   [Ask something...] │
│         (sparklines or area)             │                      │
│                                          │                      │
├──────────────────────────────────────────┴──────────────────────┤
│  BOTTOM BAR: Shock Feed / Event Log                             │
│  [12:03:45] REGULATION shock (sev: 0.7) → COMPLIANCE +, AML -  │
│  [12:03:12] Signal: "EU AI Act enforcement" (GDELT, tone: -6.2)│
│  [12:02:58] Market tick #145 — total cap: $48,230              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Header Bar
- App title + logo
- Total market cap (live, updates every tick)
- Action buttons:
  - **Inject Shock** (dropdown): Regulation Crackdown, Cyber Attack, FX Spike, Earthquake, Sanctions
  - **Run Analysis**: Calls Market Analyst, shows result in chat panel
  - **Run Tests**: Triggers TestSprite, shows pass/fail toast
  - **Graph View**: Opens Neo4j visualization (new tab or modal)
  - **(Optional) Datadog**: Link to Datadog dashboard

### 2. Agent Market Table
Columns:
| Column | Source | Format |
|--------|--------|--------|
| Agent Name | agent.name | text |
| Sector | agent.sector | badge/chip |
| Price | agent.price | $XXX.XX |
| 24h Change | computed | +X.X% (green) / -X.X% (red) |
| Volatility | agent.volatility | 0.XXX |
| Market Cap | agent.market_cap | $XX.XK |
| Inflow | agent.inflow_velocity | arrow up/down + value |
| Risk | agent.risk_score | colored bar (green/yellow/red) |

- Click a row to expand: shows mini price chart + fundamentals detail
- Sort by any column
- Color-code sector badges: FRAUD_AML=red, COMPLIANCE=blue, GEO_OSINT=green

### 3. CopilotKit Chat Panel
Integration with CopilotKit:
- **Backend action**: `useCopilotAction` to call `/copilot/chat` endpoint
- **Read state**: `useCopilotReadable` to expose current market snapshot to the copilot context
- Pre-seeded suggestions:
  - "Why did Agent X pump?"
  - "What's the safest allocation now?"
  - "Which sector is most at risk?"
  - "Summarize the last shock impact"

The chat panel forwards questions to the Bedrock Market Analyst agent with current market context.

### 4. Event Log (Bottom Bar)
Scrolling log of recent events:
- Shock injections (red)
- Signal arrivals (yellow)
- Market ticks (gray)
- Analysis results (blue)
- Test results (green/red)

Max 50 entries, auto-scroll to latest.

### 5. Graph View (Neo4j)
Two options:

**Option A (fast)**: Link button opens Neo4j Browser/Bloom in new tab with a pre-configured query.

**Option B (embedded)**: Use `neovis.js` to render a graph in a modal/panel within the app.
```
Config:
  - Node colors by label (User=blue, Agent=orange, Pool=green, Sector=purple, Shock=red)
  - Node size by market_cap (agents) or total_allocated (users)
  - Edge thickness by amount
  - On shock: highlight contagion path in red
```

Recommendation: Start with Option A, upgrade to B if time allows.

---

## API Endpoints (UI calls these)

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `/market/agents` | GET | All agents with current state | `Agent[]` |
| `/market/agents/:id` | GET | Single agent detail + history | `AgentDetail` |
| `/market/snapshot` | GET | Full market snapshot | `MarketSnapshot` |
| `/market/stream` | WS | Real-time price updates | SSE/WS stream |
| `/shock/inject` | POST | Inject a shock event | `ShockEvent` |
| `/analysis/run` | POST | Run Bedrock Market Analyst | `AnalysisResult` |
| `/analysis/risk` | POST | Run Bedrock Risk Agent | `RiskResult` |
| `/copilot/chat` | POST | CopilotKit chat endpoint | `ChatResponse` |
| `/graph/contagion` | GET | Get contagion path data | `GraphData` |
| `/tests/run` | POST | Run TestSprite tests | `TestResults` |

### WebSocket Stream (`/market/stream`)
Pushes every market tick:
```json
{
  "type": "tick",
  "tick_number": 145,
  "agents": [
    {"id": "fraudguard_v3", "price": 138.20, "change_pct": -0.8, "inflow": -0.05}
  ],
  "total_market_cap": 48230.0,
  "active_shocks": 1
}
```

Also pushes events:
```json
{
  "type": "shock",
  "shock": {"type": "REGULATION", "severity": 0.7, "description": "..."}
}
```

---

## CopilotKit Integration Details

### Provider Setup (layout.tsx)
```
<CopilotKit runtimeUrl="/api/copilotkit">
  <CopilotSidebar>
    <App />
  </CopilotSidebar>
</CopilotKit>
```

### Readable State
```
useCopilotReadable({
  description: "Current market state",
  value: marketSnapshot  // refreshed every tick
})
```

### Actions
```
useCopilotAction({
  name: "analyzeMarket",
  description: "Run the Market Analyst on current state",
  handler: async () => {
    const result = await fetch("/analysis/run", {method: "POST"})
    return result.text
  }
})

useCopilotAction({
  name: "injectShock",
  description: "Inject a shock event",
  parameters: [
    { name: "type", type: "string", enum: ["REGULATION", "CYBER", "FX_SHOCK", "EARTHQUAKE", "SANCTIONS"] }
  ],
  handler: async ({type}) => {
    await fetch("/shock/inject", {method: "POST", body: JSON.stringify({type})})
  }
})
```
