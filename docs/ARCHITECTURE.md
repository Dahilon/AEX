# Architecture

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         OPERATOR CONSOLE (UI)                          │
│                    Next.js + CopilotKit + Neo4j Viz                    │
│  ┌──────────┐  ┌──────────────┐  ┌───────────┐  ┌──────────────────┐  │
│  │ Market   │  │ Inject Shock │  │ Run       │  │ CopilotKit Chat  │  │
│  │ Table    │  │ Dropdown     │  │ Analysis  │  │ "Why did X pump?"│  │
│  └────┬─────┘  └──────┬───────┘  └─────┬─────┘  └────────┬─────────┘  │
│       │               │                │                  │            │
└───────┼───────────────┼────────────────┼──────────────────┼────────────┘
        │               │                │                  │
   REST/WS          REST POST        REST POST          REST POST
        │               │                │                  │
┌───────▼───────────────▼────────────────▼──────────────────▼────────────┐
│                          API GATEWAY (FastAPI)                          │
│                                                                        │
│  GET /market/agents          POST /shock/inject                        │
│  GET /market/agents/:id      POST /analysis/run                        │
│  GET /market/snapshot        GET  /graph/contagion                     │
│  WS  /market/stream          POST /copilot/chat                        │
└──┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────────┘
   │          │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼          ▼
┌──────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Ingest│ │ Shock  │ │Market  │ │Bedrock │ │ Graph  │ │MiniMax │
│Svc   │ │Engine  │ │Engine  │ │Agents  │ │ Svc    │ │(opt)   │
└──┬───┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
   │         │          │          │          │          │
   ▼         ▼          ▼          ▼          ▼          ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          DATA / INFRA LAYER                          │
│                                                                      │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ S3      │  │ DynamoDB │  │ Neo4j    │  │ Amazon Bedrock       │  │
│  │ Signal  │  │ or In-Mem│  │ Aura     │  │ (Claude/Nova)        │  │
│  │ Replay  │  │ State    │  │ Graph DB │  │ Converse API         │  │
│  └─────────┘  └──────────┘  └──────────┘  └──────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                     Datadog Agent                             │    │
│  │  ddtrace auto-instrumentation + custom metrics + LLM Obs     │    │
│  └──────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
External Signals                    Operator Actions
(GDELT, USGS, FX)                  (Inject Shock, Run Analysis)
       │                                    │
       ▼                                    ▼
  ┌─────────┐                        ┌───────────┐
  │ Ingest  │──SignalEvent──────────▶│  Shock    │
  │ Service │                        │  Engine   │
  └─────────┘                        └─────┬─────┘
                                           │
                                      ShockEvent
                                           │
                                           ▼
                                    ┌───────────┐
                                    │  Market   │──price updates──▶ Neo4j
                                    │  Engine   │──metrics──────▶ Datadog
                                    └─────┬─────┘
                                          │
                                     market state
                                          │
                              ┌───────────┼───────────┐
                              ▼           ▼           ▼
                         ┌────────┐ ┌────────┐ ┌────────┐
                         │Bedrock │ │  API   │ │MiniMax │
                         │Agents  │ │(to UI) │ │(voice) │
                         └────────┘ └────────┘ └────────┘
```

## AWS Services Used

| Service | Purpose | Required? |
|---------|---------|-----------|
| **Amazon Bedrock** | LLM inference for Market Analyst + Risk Agent | YES |
| **S3** | Store signal snapshots for demo replay fallback | YES |
| **EventBridge** | Schedule signal polling every 5 min | P1 |
| **Lambda** | Signal poller functions | P1 |
| **ECS Fargate** | Run FastAPI backend | PREFERRED |
| **CloudWatch** | Basic logging (Datadog primary) | FALLBACK |
| **DynamoDB** | Persist agent state + price history | OPTIONAL (can use in-memory for demo) |

## Deployment Options

### Option A: Full AWS (Production-like)
- ECS Fargate for FastAPI backend
- Lambda for signal pollers
- EventBridge for scheduling
- S3 for replay data
- Neo4j Aura (hosted, free tier)

### Option B: Local + Cloud Hybrid (Hackathon Fast)
- FastAPI runs locally or on a single EC2
- Signal polling is a background thread (not Lambda)
- In-memory state (dict/sqlite) instead of DynamoDB
- Neo4j Aura (hosted, free tier)
- S3 only for replay snapshots

**Recommendation**: Start with Option B for speed, upgrade to A if time permits.

## Key Design Decisions

1. **In-memory state for demo**: Agent prices, fundamentals, and market state live in a Python dict. Fast, no DB setup, easy to reset. Persist snapshots to S3 for replay.

2. **Single FastAPI process**: One process handles API, market engine ticks, and shock processing. Use background tasks or a simple event loop. No need for message queues at hackathon scale.

3. **Neo4j for reads, not writes-heavy**: We batch-write graph state after market ticks (every few seconds). Reads happen on-demand for contagion queries and visualization.

4. **Bedrock via Converse API**: Use `bedrock-runtime` `converse()` with tool definitions. No need for Bedrock Agents managed service — direct API is simpler and more controllable.

5. **Datadog via ddtrace + DogStatsD**: Auto-instrument FastAPI with ddtrace. Emit custom market metrics via DogStatsD. Use LLM Observability SDK for Bedrock call tracing.
