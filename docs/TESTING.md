# Testing (TestSprite)

## Overview

We use TestSprite for automated behavior testing of the market simulation. These tests validate that the market model behaves correctly — that shocks move prices in the right direction, inflows affect prices, and risk detection works.

Tests must be **runnable from a button in the UI or from CLI** and produce a clear pass/fail artifact for judges.

---

## Test 1: Inflow -> Price Rule

**What it validates**: When capital flows into an agent, its price must increase.

### Setup
```
Initial state:
  Agent: "FraudGuard-v3"
  Initial price: $142.50
  Initial inflow_velocity: 0.0

Action:
  Simulate 5 consecutive "buy" events totaling $5,000
  Run 3 market ticks
```

### Expected Outcome
```
After 3 ticks:
  inflow_velocity > 0.0
  price > $142.50
  price_increase_pct >= 1.0%  (at least 1% up)
```

### Pass/Fail Conditions
| Condition | Pass | Fail |
|-----------|------|------|
| Price increased | price_after > price_before | price_after <= price_before |
| Minimum increase | price_change_pct >= 1.0% | price_change_pct < 1.0% |
| Inflow recorded | inflow_velocity > 0 | inflow_velocity <= 0 |

### Test Contract (for TestSprite)
```json
{
  "test_name": "inflow_price_rule",
  "description": "Capital inflow must increase agent price",
  "preconditions": {
    "agent_id": "fraudguard_v3",
    "initial_price": 142.50,
    "initial_inflow_velocity": 0.0
  },
  "actions": [
    {"type": "buy", "agent_id": "fraudguard_v3", "amount": 1000, "count": 5}
  ],
  "ticks": 3,
  "assertions": [
    {"field": "price", "operator": "gt", "value": 142.50},
    {"field": "price_change_pct", "operator": "gte", "value": 1.0},
    {"field": "inflow_velocity", "operator": "gt", "value": 0.0}
  ]
}
```

---

## Test 2: Shock -> Sector Rule

**What it validates**: A REGULATION shock should cause COMPLIANCE agents to outperform FRAUD_AML agents.

### Setup
```
Initial state:
  All agents at seed prices (see MARKET_MODEL.md)
  No active shocks

Action:
  Inject ShockEvent:
    type: "REGULATION"
    severity: 0.7
    impacted_sector: "COMPLIANCE" (positive), "FRAUD_AML" (negative)
  Run 5 market ticks (allow shock to propagate)
```

### Expected Outcome
```
After 5 ticks:
  COMPLIANCE sector avg price change > 0% (positive)
  FRAUD_AML sector avg price change < 0% (negative)
  COMPLIANCE avg outperforms FRAUD_AML avg by >= 3%
```

### Pass/Fail Conditions
| Condition | Pass | Fail |
|-----------|------|------|
| Compliance up | compliance_avg_change > 0% | compliance_avg_change <= 0% |
| Fraud/AML down | fraud_aml_avg_change < 0% | fraud_aml_avg_change >= 0% |
| Relative outperformance | spread >= 3% | spread < 3% |

### Test Contract (for TestSprite)
```json
{
  "test_name": "shock_sector_rule",
  "description": "Regulation shock: Compliance outperforms Fraud/AML",
  "preconditions": {
    "agents": "seed_defaults",
    "active_shocks": 0
  },
  "actions": [
    {
      "type": "inject_shock",
      "shock_type": "REGULATION",
      "severity": 0.7
    }
  ],
  "ticks": 5,
  "assertions": [
    {"field": "sector_avg_change.COMPLIANCE", "operator": "gt", "value": 0},
    {"field": "sector_avg_change.FRAUD_AML", "operator": "lt", "value": 0},
    {
      "field": "sector_spread.COMPLIANCE_vs_FRAUD_AML",
      "operator": "gte",
      "value": 3.0
    }
  ]
}
```

---

## Test 3 (Bonus): Cascade Detection

**What it validates**: When concentration risk is high, the Risk Agent flags it.

### Setup
```
Initial state:
  One CapitalPool ("Whale Fund") backs Agent "GeoIntel-Live" with 80% of its total backing (HHI > 0.6)

Action:
  Call Risk Agent analysis
```

### Expected Outcome
```
Risk Agent output contains:
  - RISK LEVEL: MEDIUM or higher
  - Mention of "concentration" or "concentrated"
  - Reference to GeoIntel-Live or GEO_OSINT
```

### Pass/Fail Conditions
| Condition | Pass | Fail |
|-----------|------|------|
| Risk level flagged | Level >= MEDIUM | Level = LOW |
| Concentration mentioned | Output contains "concentrat" | No mention |
| Correct agent identified | Output references GeoIntel | Wrong agent |

---

## Execution

### CLI
```bash
# Run all tests
python -m tests.run_testsprite

# Run specific test
python -m tests.run_testsprite --test inflow_price_rule
python -m tests.run_testsprite --test shock_sector_rule
```

### UI Button
The "Run Tests" button in the Operator Console calls:
```
POST /tests/run
Body: { "test_name": "all" | "inflow_price_rule" | "shock_sector_rule" }
```

Response:
```json
{
  "results": [
    {
      "test_name": "inflow_price_rule",
      "status": "PASS",
      "duration_ms": 450,
      "details": {
        "price_before": 142.50,
        "price_after": 145.12,
        "price_change_pct": 1.84,
        "inflow_velocity": 0.23
      }
    },
    {
      "test_name": "shock_sector_rule",
      "status": "PASS",
      "duration_ms": 820,
      "details": {
        "compliance_avg_change": 4.2,
        "fraud_aml_avg_change": -2.8,
        "spread": 7.0
      }
    }
  ],
  "summary": "2/2 PASSED"
}
```

### Screenshot Artifact
For judges, the test result card in the UI shows:
- Green checkmark or red X per test
- Key metrics from the test
- Timestamp
- This is also a screenshot-able artifact
