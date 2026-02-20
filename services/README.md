# /services — Backend (Python / FastAPI)

## Structure (to be created)
```
services/
├── api/
│   ├── main.py              # FastAPI app, routes, CORS, WebSocket
│   └── models.py            # Pydantic request/response models
├── market_engine/
│   ├── engine.py             # MarketEngine class, tick loop, pricing
│   ├── models.py             # Agent, Sector, MarketState dataclasses
│   └── seed_data.py          # Initial 8 agents, 3 sectors
├── shock_engine/
│   ├── engine.py             # SignalEvent -> ShockEvent conversion
│   └── sector_betas.py       # Shock type -> sector sensitivity matrix
├── agents/
│   ├── market_analyst.py     # Bedrock Market Analyst agent
│   ├── risk_agent.py         # Bedrock Risk Agent
│   └── tools.py              # market_snapshot() and graph_query() tool implementations
├── graph/
│   ├── service.py            # Neo4j driver, query execution
│   ├── seed.py               # Seed graph with Users, Pools, Agents, Sectors
│   └── queries.py            # Cypher query definitions
├── ingestion/
│   ├── gdelt.py              # GDELT poller + normalizer
│   ├── usgs.py               # USGS earthquake poller
│   ├── fx.py                 # FX rate poller
│   └── replay.py             # S3 replay loader
├── observability/
│   ├── metrics.py            # Custom Datadog metric emission
│   └── tracing.py            # Span helpers, LLM Obs setup
└── minimax/
    └── tts.py                # MiniMax TTS integration (optional)
```

## Setup (when implementing)
```bash
cd services
python -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn boto3 neo4j ddtrace datadog pydantic httpx
```

## Running
```bash
DD_SERVICE=aex DD_ENV=demo ddtrace-run uvicorn services.api.main:app --host 0.0.0.0 --port 8000
```
