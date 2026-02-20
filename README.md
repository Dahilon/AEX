# AEX: Agent Exchange & Capital Flow Engine

> A real-time "stock market for AI agents" where agents are tradable assets, prices move on usage + performance + external shocks, and capital contagion is visualized as a live network graph.

## Why AEX Wins

| Criteria | How AEX delivers |
|----------|-----------------|
| **Technical depth** | Real pricing model, graph-based contagion analysis, Bedrock agents with tools, custom Datadog metrics + LLM observability |
| **AWS integration** | Amazon Bedrock (required), S3 for signal replay, Lambda/ECS for services, EventBridge for scheduling |
| **Observability story** | Not bolted on — market metrics ARE the observability. Shock severity, cascade probability, token usage all on one dashboard |
| **Partner value** | Neo4j = capital flow graph (not just a DB). TestSprite = behavior validation. CopilotKit = operator console. MiniMax = voice market brief |
| **Demo impact** | Inject a shock -> watch prices move -> see graph light up -> hear Bedrock explain why -> metrics spike on Datadog |

## Demo Flow (2 minutes)

1. **Open** the Operator Console (CopilotKit UI)
2. **Show** the Agent Market table — 8 agents, live prices, sectors
3. **Inject** a "Regulation Crackdown" shock via dropdown
4. **Watch** Compliance sector agents spike, Fraud/AML agents drop
5. **Switch** to Neo4j graph — capital flows reroute, contagion path highlighted
6. **Click** "Run Analysis" — Bedrock Market Analyst explains the move
7. **Open** Datadog dashboard — shock severity spike, cascade probability rising, LLM token usage visible
8. **Run** TestSprite test — "Shock -> Sector Rule" passes green
9. **(Optional)** MiniMax voice summary: "Today's market saw a regulation shock..."

## Sponsor Integration Checklist

| Sponsor | Integration | Required? |
|---------|------------|-----------|
| **AWS (Bedrock)** | Market Analyst Agent + Risk Agent via Bedrock Converse API | YES |
| **Datadog** | LLM Observability + custom market metrics + dashboard | YES |
| **Neo4j** | Capital flow graph (Users -> Pools -> Agents -> Sectors) | YES |
| **TestSprite** | Automated behavior tests (inflow->price, shock->sector) | YES |
| **CopilotKit** | Operator Console UI with chat panel | YES |
| **MiniMax** | Voice market summary (optional wow factor) | OPTIONAL |

## Tech Stack

- **Backend**: Python 3.12 (FastAPI)
- **Frontend**: Next.js + CopilotKit
- **AI**: Amazon Bedrock (Claude / Nova)
- **Graph DB**: Neo4j Aura (free tier)
- **Observability**: Datadog (ddtrace + datadog-api-client)
- **Testing**: TestSprite
- **Infra**: AWS CDK or manual deploy (ECS Fargate / Lambda)

## Project Structure

```
AEX/
├── README.md
├── docs/                    # All technical specs
│   ├── ARCHITECTURE.md
│   ├── DATA_SOURCES.md
│   ├── MARKET_MODEL.md
│   ├── GRAPH_SCHEMA.md
│   ├── AGENTS_SPEC.md
│   ├── OBSERVABILITY.md
│   ├── TESTING.md
│   ├── UI_SPEC.md
│   ├── MINIMAX_SPEC.md
│   ├── DEMO_SCRIPT.md
│   └── TASKS.md
├── backend/                 # Backend services
│   └── services/
│       ├── api/             # FastAPI app
│       ├── ingestion/       # Signal pollers
│       ├── shock_engine/    # ShockEvent processing
│       ├── market_engine/   # Valuation + price updates
│       ├── agents/          # Bedrock agent wrappers
│       └── graph/           # Neo4j queries
├── frontend/                # Frontend UI
│   └── ui/                  # Next.js + CopilotKit frontend
├── infra/                   # AWS CDK / deploy scripts
├── tests/                   # TestSprite + unit tests
├── run_backend.sh           # Start backend server
├── run_frontend.sh          # Start frontend server
└── seed_neo4j.sh            # Seed Neo4j graph
```

## Quick Start

```bash
# (instructions will be added once services are implemented)
```

## Team

Built for the AWS Hackathon 2025.
