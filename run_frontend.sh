#!/bin/bash
# Start AEX frontend (Next.js)
# Run from repo root.

set -e

cd "$(dirname "$0")/frontend/ui"
echo "Working directory: $(pwd)"

if [ -f .env.local.example ] && [ ! -f .env.local ]; then
  echo "⚠️  frontend/ui/.env.local not found. Copying from .env.local.example..."
  cp .env.local.example .env.local
  echo "   Edit frontend/ui/.env.local if needed (e.g. NEXT_PUBLIC_API_URL)"
fi

if [ ! -d node_modules ]; then
  echo "Installing npm dependencies (this may take a minute)..."
  npm install
  echo "✅ npm install done."
fi

echo "✅ Starting AEX frontend on http://localhost:3000"
echo "   Open http://localhost:3000 in your browser once you see 'Ready' below."
npm run dev
