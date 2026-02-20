# Tasks — 6-Hour Build Plan

## Priority Definitions
- **P0**: Must complete. Without these, no demo.
- **P1**: Should complete. Adds real value and polish.
- **P2**: Nice to have. Wow factor if time permits.

---

## Hour 1 (0:00-1:00) — Foundation

### P0: Market Engine Core
- [ ] Define data models: Agent, Sector, ShockEvent, MarketState (Python dataclasses/Pydantic)
- [ ] Implement pricing formula (see MARKET_MODEL.md)
- [ ] Implement market tick loop (2-second interval)
- [ ] Seed 8 agents with initial fundamentals
- [ ] Implement shock application with sector beta matrix
- [ ] Implement shock decay (4-tick decay curve)
**Owner**: Backend Dev 1
**Deliverable**: `python -c "from services.market_engine import MarketEngine; m = MarketEngine(); m.tick()"` works

### P0: FastAPI Skeleton
- [ ] Set up FastAPI app with CORS
- [ ] `GET /market/agents` — returns all agents
- [ ] `GET /market/snapshot` — returns full state
- [ ] `POST /shock/inject` — accepts shock type, creates ShockEvent, applies to engine
- [ ] WebSocket `/market/stream` — pushes tick updates
**Owner**: Backend Dev 2
**Deliverable**: `curl localhost:8000/market/agents` returns JSON

---

## Hour 2 (1:00-2:00) — Bedrock + Neo4j

### P0: Bedrock Market Analyst Agent
- [ ] Implement Bedrock Converse API call with tool definitions
- [ ] Implement `market_snapshot` tool (returns current state)
- [ ] Implement `graph_query` tool (stub first, Neo4j later)
- [ ] Wire system prompt from AGENTS_SPEC.md
- [ ] `POST /analysis/run` endpoint
- [ ] Add ddtrace LLM Observability wrapping
**Owner**: Backend Dev 1
**Deliverable**: Hit `/analysis/run`, get Bedrock analysis text back

### P0: Neo4j Graph Setup
- [ ] Create Neo4j Aura free instance
- [ ] Write seed script: create Users, Pools, Agents, Sectors, edges
- [ ] Implement graph_service.py with neo4j Python driver
- [ ] Implement 3 key queries: top_inflow, concentration_risk, contagion_path
- [ ] `GET /graph/contagion` endpoint
- [ ] Wire `graph_query` tool to real Neo4j
**Owner**: Backend Dev 2
**Deliverable**: Neo4j Browser shows seeded graph, `/graph/contagion` returns data

---

## Hour 3 (2:00-3:00) — UI + Datadog

### P0: Operator Console UI
- [ ] Next.js project setup with CopilotKit
- [ ] Market table component (fetches `/market/agents`, polls or WS)
- [ ] "Inject Shock" dropdown (calls `/shock/inject`)
- [ ] "Run Analysis" button (calls `/analysis/run`, shows result)
- [ ] Event log at bottom (shows shocks, ticks)
- [ ] Basic styling (Tailwind, dark theme for market vibe)
**Owner**: Frontend Dev
**Deliverable**: UI loads, table shows agents, shock injection works end-to-end

### P0: Datadog Integration
- [ ] Install ddtrace, configure DD_SERVICE, DD_ENV
- [ ] Wrap FastAPI with ddtrace-run
- [ ] Emit custom metrics: aex.agent.price, aex.agent.volatility, aex.shock.severity, aex.market.cascade_probability
- [ ] Emit LLM Observability spans for Bedrock calls
- [ ] Create Datadog dashboard with 5 rows (see OBSERVABILITY.md)
**Owner**: Backend Dev 1 (metrics) + anyone (dashboard)
**Deliverable**: Datadog dashboard shows agent prices and shock events

---

## Hour 4 (3:00-4:00) — Integration + CopilotKit Chat

### P0: End-to-End Integration
- [ ] Verify: inject shock → prices move → graph updates → Bedrock explains → Datadog shows
- [ ] Fix any data flow gaps
- [ ] Add Risk Agent (second Bedrock agent)
- [ ] `POST /analysis/risk` endpoint
**Owner**: All

### P1: CopilotKit Chat Panel
- [ ] Set up CopilotKit runtime endpoint
- [ ] `useCopilotReadable` with market snapshot
- [ ] `useCopilotAction` for analyzeMarket and injectShock
- [ ] Chat panel in sidebar
- [ ] Pre-seeded suggestion chips
**Owner**: Frontend Dev
**Deliverable**: Can ask "Why did CompliBot pump?" and get answer

### P1: Graph Visualization in UI
- [ ] Option A: Link to Neo4j Browser (fast)
- [ ] Option B: Embed neovis.js in a modal (if time)
**Owner**: Frontend Dev

---

## Hour 5 (4:00-5:00) — Signal Ingestion + Testing

### P1: Real Signal Ingestion
- [ ] GDELT poller: fetch, normalize to SignalEvent
- [ ] USGS poller: fetch, normalize to SignalEvent
- [ ] FX poller: fetch, normalize to SignalEvent
- [ ] Signal → ShockEvent conversion logic
- [ ] Replay mode: load from curated JSON
- [ ] Toggle: SIGNAL_MODE=live|replay
- [ ] Upload curated snapshot to S3
**Owner**: Backend Dev 2
**Deliverable**: Signals arrive, convert to shocks, move prices

### P0: TestSprite Tests
- [ ] Implement test runner: inflow_price_rule
- [ ] Implement test runner: shock_sector_rule
- [ ] `POST /tests/run` endpoint
- [ ] "Run Tests" button in UI
- [ ] Verify both tests pass
**Owner**: Backend Dev 1
**Deliverable**: Both tests pass, result shown in UI

---

## Hour 6 (5:00-6:00) — Polish + Demo Prep

### P1: Polish
- [ ] Market table: color coding, sort, expand row for detail
- [ ] Mini price sparklines in table
- [ ] Event log styling
- [ ] Dashboard fine-tuning (time windows, colors, thresholds)
- [ ] Error handling: fallbacks for all external calls

### P2: MiniMax Voice Summary
- [ ] Implement `/audio/summary` endpoint
- [ ] Call MiniMax TTS API
- [ ] "Play Audio Summary" button in UI
- [ ] Fallback: hide button if unavailable
**Owner**: Anyone with time
**Deliverable**: Voice plays after analysis

### P0: Demo Rehearsal
- [ ] Run through DEMO_SCRIPT.md 2-3 times
- [ ] Verify fallback mode works (switch to replay, cached analysis)
- [ ] Take screenshots of: market table, graph, dashboard, test results
- [ ] Pre-warm Bedrock (make a test call)
- [ ] Set Datadog dashboard to correct time window

---

## Summary

| Priority | Tasks | Must finish by |
|----------|-------|---------------|
| **P0** | Market engine, API, Bedrock agent, Neo4j, UI table, Shock inject, Datadog dashboard, Tests, Demo rehearsal | Hour 5 |
| **P1** | CopilotKit chat, Graph viz in UI, Signal ingestion, UI polish | Hour 6 |
| **P2** | MiniMax voice, Extra dashboard widgets, Mobile responsive | If time |

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Bedrock cold start | Pre-warm 5 min before demo |
| Neo4j Aura slow | Pre-load graph, cache queries |
| Signal APIs down | Replay mode from S3 |
| MiniMax fails | It's optional, skip gracefully |
| Datadog metric delay | Metrics usually appear in <30s; if delayed, show recent window |
| Demo laptop dies | Have backup laptop with same env, or deploy to EC2 |
