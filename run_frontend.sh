#!/bin/bash
# Start AEX frontend (Next.js)
# Run from repo root.

set -e

cd "$(dirname "$0")/ui"

if [ -f .env.local.example ] && [ ! -f .env.local ]; then
  echo "⚠️  ui/.env.local not found. Copying from .env.local.example..."
  cp .env.local.example .env.local
  echo "   Edit ui/.env.local and set ANTHROPIC_API_KEY"
fi

if [ ! -d node_modules ]; then
  echo "Installing npm dependencies..."
  npm install
fi

echo "✅ Starting AEX frontend on http://localhost:3000"
npm run dev
