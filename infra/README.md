# /infra — Infrastructure

## Contents (to be created)

- AWS CDK stack or deployment scripts
- Environment variable templates (.env.example)
- Neo4j Aura setup notes
- Datadog agent configuration
- S3 bucket setup for signal replay

## AWS Services to Configure

| Service | Resource | Notes |
|---------|----------|-------|
| Bedrock | Model access for Claude 3.5 Sonnet or Nova Pro | Enable in us-east-1 |
| S3 | `aex-signals` bucket | Store replay snapshots |
| ECS Fargate | Service for FastAPI (optional, can run local) | Only if deploying to cloud |
| EventBridge | Schedule rule for signal polling (P1) | Every 5 min |

## Environment Variables Needed

```
# AWS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# Neo4j
NEO4J_URI=neo4j+s://<instance>.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=

# Datadog
DD_API_KEY=
DD_APP_KEY=
DD_SERVICE=aex
DD_ENV=demo

# MiniMax (optional)
MINIMAX_API_KEY=
MINIMAX_GROUP_ID=
MINIMAX_ENABLED=false

# App
SIGNAL_MODE=replay
MARKET_TICK_INTERVAL_MS=2000
```
