#!/bin/bash
# Seed Neo4j with demo graph data.
# Run ONCE before demo.

set -e

cd "$(dirname "$0")"

if [ -f services/.env ]; then
  export $(grep -v '^#' services/.env | xargs)
fi

source .venv/bin/activate 2>/dev/null || true

echo "🌱 Seeding Neo4j graph..."
python -m services.graph.seed
echo "✅ Neo4j graph seeded!"
