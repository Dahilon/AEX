# Market Model

## Agent Fundamentals

Each agent has a set of fundamentals that drive its price. These are updated every market tick (every 2-5 seconds during demo).

```
AgentFundamentals {
  agent_id: str
  sector: "FRAUD_AML" | "COMPLIANCE" | "GEO_OSINT"

  # Core scores (0.0 - 1.0)
  usage_score: float         # how much this agent is being used
  performance_score: float   # task success rate / quality
  reliability_score: float   # uptime, latency consistency
  risk_score: float          # higher = riskier (bad)

  # Flow metrics
  inflow_velocity: float     # net capital inflow rate (can be negative)
  total_backing: float       # total capital allocated to this agent

  # Derived
  volatility: float          # rolling std dev of price changes (20-tick window)
  market_cap: float          # price * total_backing
}
```

## Initial Agent Roster (Demo Seed Data)

| Agent | Sector | Usage | Perf | Reliability | Risk | Initial Price |
|-------|--------|-------|------|-------------|------|---------------|
| FraudGuard-v3 | FRAUD_AML | 0.85 | 0.78 | 0.92 | 0.35 | $142.50 |
| AMLScan-Pro | FRAUD_AML | 0.72 | 0.81 | 0.88 | 0.42 | $98.30 |
| TxnMonitor | FRAUD_AML | 0.65 | 0.70 | 0.95 | 0.28 | $76.00 |
| CompliBot-EU | COMPLIANCE | 0.90 | 0.85 | 0.90 | 0.20 | $210.00 |
| RegWatch-US | COMPLIANCE | 0.78 | 0.82 | 0.87 | 0.25 | $165.40 |
| SanctionScreen | COMPLIANCE | 0.60 | 0.75 | 0.93 | 0.30 | $88.00 |
| GeoIntel-Live | GEO_OSINT | 0.70 | 0.68 | 0.80 | 0.55 | $55.20 |
| ThreatMapper | GEO_OSINT | 0.55 | 0.62 | 0.75 | 0.60 | $42.80 |

## Pricing Formula

Price updates every tick:

```
price_t = price_{t-1} * (1 + delta)

where:
  delta = alpha * inflow_velocity
        + beta  * performance_delta
        - gamma * risk_delta
        + shock_impact
        + noise

Parameters:
  alpha = 0.15    # inflow sensitivity
  beta  = 0.10    # performance sensitivity
  gamma = 0.12    # risk penalty
  noise ~ N(0, 0.005)  # random walk component
```

### Parameter Explanation

- **alpha (inflow sensitivity)**: When capital flows into an agent, price goes up. `inflow_velocity` is normalized to [-1, +1].
- **beta (performance sensitivity)**: `performance_delta` = change in performance_score since last tick. Reward improving agents.
- **gamma (risk penalty)**: `risk_delta` = change in risk_score. Penalize agents becoming riskier.
- **shock_impact**: Computed by the Shock Engine (see below). Can be positive or negative.
- **noise**: Small random component to make charts look realistic.

### Price Bounds
- Floor: $1.00 (agent never goes to zero)
- Ceiling: none (but practical cap ~$1000 for demo)
- If price < $5.00, flag as "penny agent" in UI

## Shock Impact Calculation

When a ShockEvent hits:

```
shock_impact = severity * sector_beta * direction

where:
  severity: 0.0 - 1.0 (from SignalEvent)
  sector_beta: how sensitive this sector is to this shock type
  direction: +1 (benefits) or -1 (hurts)
```

### Sector Beta Matrix

| Shock Type | FRAUD_AML | COMPLIANCE | GEO_OSINT |
|-----------|-----------|------------|-----------|
| REGULATION | -0.6 | +0.8 | -0.2 |
| CYBER | +0.5 | -0.3 | +0.7 |
| FX_SHOCK | -0.4 | -0.2 | -0.3 |
| EARTHQUAKE | -0.2 | -0.1 | +0.6 |
| SANCTIONS | +0.3 | +0.7 | +0.5 |

**Reading the matrix**: REGULATION shock with severity 0.7:
- FRAUD_AML agents: shock_impact = 0.7 * (-0.6) = -0.42 → price drops ~42%... but clamped.

### Shock Impact Clamp
- Max single-tick impact: +/- 0.15 (15%)
- This prevents unrealistic jumps. Shocks propagate over 3-5 ticks with decay:
  - tick 0: full impact
  - tick 1: impact * 0.6
  - tick 2: impact * 0.3
  - tick 3: impact * 0.1
  - tick 4+: 0

## Volatility Calculation

Rolling 20-tick standard deviation of price returns:

```
returns = [ln(price_t / price_{t-1}) for t in last_20_ticks]
volatility = std(returns)
```

For demo seeding, pre-populate 20 ticks of synthetic history with slight random walk.

## Inflow Velocity

Driven by user "buy/sell" events:

```
inflow_velocity_t = (sum_of_buys - sum_of_sells) / total_backing

# Normalized to [-1, +1]
# Decays toward 0 if no new activity: inflow_velocity *= 0.95 each tick
```

For demo, we simulate 20-50 users making random allocations biased by:
- Sector sentiment (post-shock, users pile into winning sectors)
- Herding: 30% chance a user copies the last 3 trades

## Market Cap

```
market_cap = price * total_backing
```

Total market cap = sum of all agent market caps. Displayed in UI header.

## Manipulation Detection Heuristic

The Risk Agent checks for:

1. **Concentration Risk (Herfindahl Index)**:
   ```
   HHI = sum((pool_amount / total_backing)^2 for each pool backing this agent)
   if HHI > 0.4 → flag "Concentrated Backing"
   ```

2. **Wash Trading Pattern**:
   ```
   if same user buys and sells same agent within 3 ticks:
     flag "Potential Wash Trade"
   ```

3. **Pump Detection**:
   ```
   if inflow_velocity > 0.7 AND volatility < 0.02:
     flag "Unusual Low-Vol Pump" (suspicious steady buying)
   ```

4. **Cascade Risk**:
   ```
   cascade_probability = max_sector_concentration * avg_cross_sector_correlation
   if cascade_probability > 0.6 → flag "Cascade Warning"
   ```

These flags appear in the Risk Agent's analysis output and on the Datadog dashboard.
