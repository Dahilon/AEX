# Work Division — AEX Hackathon

## Split: Backend (Person A) vs Frontend (Person B)

### Golden Rule
Person A owns everything in `/services/`. Person B owns everything in `/ui/`.
The contract between them is the **API spec** at the bottom of this doc.
They can work in parallel from minute one.

---

## Person A — Backend Engineer

### Your Stack
Python 3.12, FastAPI, Amazon Bedrock, Neo4j, Datadog, ddtrace

### Your Files (in order of priority)

| File | What to implement | Priority |
|------|------------------|---------|
| `services/market_engine/models.py` | Agent, Sector, ShockEvent, MarketState dataclasses | P0 |
| `services/market_engine/seed_data.py` | 8 agents, 3 sectors with initial values | P0 |
| `services/market_engine/engine.py` | Tick loop, pricing formula, shock application, decay | P0 |
| `services/shock_engine/sector_betas.py` | Beta matrix dict | P0 |
| `services/shock_engine/engine.py` | SignalEvent → ShockEvent conversion | P0 |
| `services/api/routes/market.py` | GET /market/agents, GET /market/snapshot, WS /market/stream | P0 |
| `services/api/routes/shock.py` | POST /shock/inject | P0 |
| `services/agents/tools.py` | market_snapshot() and graph_query() tool implementations | P0 |
| `services/agents/market_analyst.py` | Bedrock Converse API call, tool loop, LLM Obs | P0 |
| `services/api/routes/analysis.py` | POST /analysis/run, POST /analysis/risk | P0 |
| `services/observability/metrics.py` | DogStatsD metric emitters for all aex.* metrics | P0 |
| `services/graph/queries.py` | 5 Cypher queries as string templates | P0 |
| `services/graph/seed.py` | Neo4j seed script (run once) | P0 |
| `services/graph/service.py` | Neo4j driver wrapper, execute queries | P0 |
| `services/api/routes/graph.py` | GET /graph/contagion | P1 |
| `services/agents/risk_agent.py` | Bedrock Risk Agent (same pattern as market_analyst) | P1 |
| `services/ingestion/replay.py` | Load signals from JSON file | P1 |
| `services/ingestion/gdelt.py` | GDELT API poller | P1 |
| `services/ingestion/usgs.py` | USGS earthquake poller | P1 |
| `services/ingestion/fx.py` | FX rate poller | P1 |
| `services/api/routes/tests.py` | POST /tests/run (TestSprite runner) | P1 |
| `services/minimax/tts.py` | MiniMax TTS call | P2 |

### Your Hour-by-Hour
- **Hour 1**: models.py + seed_data.py + engine.py (market ticks working)
- **Hour 2**: Bedrock market_analyst.py + tools.py + /analysis/run working
- **Hour 3**: Neo4j seed + graph/service.py + graph queries working
- **Hour 4**: Datadog metrics emitting + all routes wired + integration test
- **Hour 5**: Signal ingestion (replay first) + TestSprite tests
- **Hour 6**: Risk Agent + polish + demo rehearsal

### How to Start Right Now
```bash
cd /Users/dusitmohammed/AWSHackthon
python -m venv .venv && source .venv/bin/activate
pip install -r services/requirements.txt
cp services/.env.example services/.env   # fill in secrets
uvicorn services.api.main:app --reload --port 8000
```

---

## Person B — Frontend Engineer

### Your Stack
Next.js 14 (App Router), TypeScript, CopilotKit, Tailwind CSS, Recharts

### Your Files (in order of priority)

| File | What to implement | Priority |
|------|------------------|---------|
| `ui/types/market.ts` | TypeScript interfaces for Agent, Shock, MarketState | P0 |
| `ui/lib/api.ts` | API client functions (fetchAgents, injectShock, runAnalysis, etc.) | P0 |
| `ui/hooks/useMarketStream.ts` | WebSocket hook for live price updates | P0 |
| `ui/app/layout.tsx` | Root layout with CopilotKit provider | P0 |
| `ui/app/page.tsx` | Main page: wires all components together | P0 |
| `ui/components/Header.tsx` | App bar with market cap + action buttons | P0 |
| `ui/components/MarketTable.tsx` | Agent table with live prices + color coding | P0 |
| `ui/components/ShockInjector.tsx` | Dropdown + inject button | P0 |
| `ui/components/AnalysisPanel.tsx` | Shows Bedrock analysis text | P0 |
| `ui/components/EventLog.tsx` | Scrolling event feed at bottom | P1 |
| `ui/components/GraphView.tsx` | Neo4j graph (link or embedded Neovis) | P1 |
| `ui/app/api/copilotkit/route.ts` | CopilotKit backend route | P1 |
| `ui/components/AudioPlayer.tsx` | MiniMax voice player (optional) | P2 |

### Your Hour-by-Hour
- **Hour 1**: Setup Next.js + Tailwind + CopilotKit. types.ts + api.ts + layout.tsx
- **Hour 2**: MarketTable component + useMarketStream hook (connect to WS)
- **Hour 3**: Header + ShockInjector + AnalysisPanel — full user flow working
- **Hour 4**: CopilotKit chat panel + copilotkit route
- **Hour 5**: EventLog + GraphView + polish (colors, sparklines)
- **Hour 6**: AudioPlayer (optional) + demo polish

### How to Start Right Now
```bash
cd /Users/dusitmohammed/AWSHackthon/ui
npm install
cp .env.local.example .env.local    # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

---

## The Contract Between A and B

### What Person A provides (API endpoints)

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/market/agents` | GET | `Agent[]` |
| `/market/snapshot` | GET | `MarketSnapshot` |
| `/market/stream` | WS | `TickUpdate` stream |
| `/shock/inject` | POST | `ShockEvent` |
| `/analysis/run` | POST | `{ text: string }` |
| `/analysis/risk` | POST | `{ text: string, risk_level: string }` |
| `/graph/contagion` | GET | `GraphData` |
| `/tests/run` | POST | `TestResults` |
| `/audio/summary` | POST | `{ audio_url: string }` |

### What Person B MUST NOT change
- API URLs (they match the backend routes exactly)
- WebSocket message format (see types/market.ts — copy from this file)

### How to unblock yourself if the API isn't ready
Person B: Mock it. `ui/lib/api.ts` has a `USE_MOCK` flag. Set to `true` and use the mock data in `ui/lib/mockData.ts`. Build the full UI against mocks, swap to real API when Person A is ready.

---

## Sync Points (do these together)
1. **After Hour 1**: Person A runs `curl localhost:8000/market/agents` → Person B sees agents in table
2. **After Hour 2**: Person A has `/analysis/run` → Person B wires "Run Analysis" button
3. **After Hour 3**: Full shock inject → prices move → analysis explains → both integrated
4. **Before Hour 6**: Full demo rehearsal together (both present)

---

## Communication Protocol
- Share a Slack/Discord thread or group chat
- When Person A's endpoint is ready: post "✅ /market/agents LIVE"
- When Person B needs a field: post "Need `inflow_direction` on Agent model"
- Don't merge breaking changes without telling each other
