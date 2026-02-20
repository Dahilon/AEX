# /ui — Frontend (Next.js + CopilotKit)

## Stack
- Next.js 14 (App Router)
- CopilotKit (@copilotkit/react-ui, @copilotkit/react-core)
- Tailwind CSS
- Recharts (price sparklines)
- Neovis.js (optional, for embedded graph)

## Setup (when implementing)
```bash
npx create-next-app@latest ui --typescript --tailwind --app
cd ui
npm install @copilotkit/react-ui @copilotkit/react-core @copilotkit/runtime
npm install recharts
```

## Pages
- `/` — Operator Console (single-page app, see UI_SPEC.md)

## Key Components (to build)
- `MarketTable` — agent list with live prices
- `ShockInjector` — dropdown to inject shocks
- `AnalysisPanel` — Bedrock analysis results
- `EventLog` — scrolling event feed
- `GraphView` — Neo4j visualization (modal or link)
- `AudioPlayer` — MiniMax voice playback (optional)

## API Connection
Backend runs at `http://localhost:8000` (FastAPI).
Configure proxy in `next.config.js` or use env var `NEXT_PUBLIC_API_URL`.
