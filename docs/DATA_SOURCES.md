# Data Sources

## Overview

AEX uses three real-world public data sources as "shock triggers" for the market simulation. These are NOT financial transaction data — they are event signals that create market-moving shocks.

All sources have a **live mode** (poll real API) and a **replay mode** (read from S3 snapshot). Replay mode is the demo fallback.

---

## 1. GDELT (Global Database of Events, Language, and Tone)

**Purpose**: Near real-time news/events metadata for regulation, sanctions, cyber, and fintech shock triggers.

**Endpoint**: `https://api.gdeltproject.org/api/v2/doc/doc?query=<terms>&mode=ArtList&maxrecords=50&format=json`

**Query terms we use**:
- `"AI regulation" OR "artificial intelligence ban"` → REGULATION shock
- `"sanctions" OR "financial sanctions"` → SANCTIONS shock
- `"cyber attack" OR "data breach"` → CYBER shock
- `"fintech" OR "AI startup funding"` → FINTECH_SENTIMENT shock

**Polling strategy**:
- Every 5 minutes
- Deduplicate by article URL
- Extract: title, source, tone score, date, themes

**Normalization to SignalEvent**:
```
SignalEvent {
  source: "GDELT"
  type: "NEWS"
  raw_title: str
  tone: float            # GDELT tone score (-10 to +10)
  themes: list[str]      # GDELT taxonomy themes
  timestamp: datetime
  url: str
}
```

**Shock mapping heuristic**:
- If themes contain "TAX" or "REGULATION" → shock_type = REGULATION
- If themes contain "CYBER" or "HACK" → shock_type = CYBER
- If tone < -5 → amplify severity by 1.5x
- Default severity = `abs(tone) / 10` clamped to [0.1, 1.0]

**Rate limits**: GDELT has no auth and no strict rate limit, but responses can be slow (2-5s). Cache aggressively.

---

## 2. USGS Earthquake GeoJSON

**Purpose**: Physical disruption triggers. Earthquakes near data center regions or financial hubs create DISRUPTION shocks.

**Endpoint**: `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_hour.geojson`

Returns all M2.5+ earthquakes in the past hour.

**Polling strategy**:
- Every 5 minutes
- Deduplicate by earthquake ID

**Normalization to SignalEvent**:
```
SignalEvent {
  source: "USGS"
  type: "EARTHQUAKE"
  magnitude: float
  location: str          # human-readable place
  lat: float
  lon: float
  depth_km: float
  timestamp: datetime
}
```

**Shock mapping heuristic**:
- magnitude >= 6.0 → severity = HIGH (0.8-1.0)
- magnitude >= 4.5 → severity = MEDIUM (0.4-0.7)
- magnitude >= 2.5 → severity = LOW (0.1-0.3)
- Impacted sector: GEO_OSINT always; FRAUD_AML if near financial hub
- "Financial hub" = within 500km of: NYC, London, Tokyo, Singapore, Frankfurt

**Rate limits**: None. Public API. Very reliable.

---

## 3. Exchange Rates (exchangerate.host)

**Purpose**: Macro volatility trigger. Large FX moves signal economic stress.

**Endpoint**: `https://api.exchangerate.host/live?access_key=<KEY>&currencies=EUR,GBP,JPY,CHF`

**Alternative (no key)**: `https://open.er-api.com/v6/latest/USD`

**Polling strategy**:
- Every 10 minutes
- Track previous values to compute delta

**Normalization to SignalEvent**:
```
SignalEvent {
  source: "FX"
  type: "FX_MOVE"
  pair: str              # e.g. "USD/EUR"
  rate: float
  delta_pct: float       # % change from last poll
  timestamp: datetime
}
```

**Shock mapping heuristic**:
- `abs(delta_pct) > 1.0%` in one poll → FX_SHOCK, severity = min(abs(delta_pct) / 3, 1.0)
- `abs(delta_pct) > 0.3%` → FX_TREMOR, severity = abs(delta_pct) / 5
- Impacted sectors: ALL (macro shock), but COMPLIANCE more resilient (lower beta)

**Rate limits**: Free tier = 100 req/month on exchangerate.host. Use open.er-api.com as fallback (no key, 1500 req/month).

---

## Replay / Fallback Strategy

For demo reliability, we pre-capture signal snapshots:

### Pre-demo Capture
1. Run each poller once and save raw JSON to S3:
   - `s3://aex-signals/gdelt/snapshot_2025.json`
   - `s3://aex-signals/usgs/snapshot_2025.json`
   - `s3://aex-signals/fx/snapshot_2025.json`

2. Also include a **curated demo snapshot** with hand-picked interesting events:
   - A regulation article about AI in EU
   - A M5.5 earthquake near Tokyo
   - A 0.8% EUR/USD move
   - `s3://aex-signals/demo/curated_signals.json`

### Runtime Toggle
```
ENV: SIGNAL_MODE=live|replay

if SIGNAL_MODE == "replay":
    load signals from S3 curated snapshot
    inject them on a timer (one every 30s for demo pacing)
else:
    poll live APIs
```

### Failure Handling
- If any live API call fails (timeout > 5s, HTTP error), log warning and auto-switch to replay for that source
- Never let a failed API call block the demo

---

## SignalEvent Unified Schema

All sources normalize to this before hitting the Shock Engine:

```
SignalEvent {
  id: str                # uuid
  source: "GDELT" | "USGS" | "FX"
  type: str              # NEWS, EARTHQUAKE, FX_MOVE
  timestamp: datetime
  severity_hint: float   # 0.0-1.0, source-specific heuristic
  metadata: dict         # source-specific fields
  raw: dict              # original API response (for debugging)
}
```
