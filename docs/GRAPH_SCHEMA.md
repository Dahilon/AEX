# Graph Schema (Neo4j)

## Purpose

The Neo4j graph models the entire AEX market as a network. Its primary value is **visualizing capital contagion**: when a shock hits, how does capital flow, which agents are impacted, and where is concentration risk?

## Node Types

### User
```
(:User {
  id: STRING,           // "user_001"
  name: STRING,         // "Alice"
  risk_profile: STRING, // "aggressive" | "moderate" | "conservative"
  total_allocated: FLOAT
})
```

### CapitalPool
```
(:CapitalPool {
  id: STRING,           // "pool_001"
  name: STRING,         // "Alpha Fund"
  total_value: FLOAT,
  strategy: STRING      // "sector_balanced" | "high_risk" | "safe_haven"
})
```

### Agent
```
(:Agent {
  id: STRING,           // "fraudguard_v3"
  name: STRING,         // "FraudGuard-v3"
  sector: STRING,       // "FRAUD_AML"
  price: FLOAT,
  market_cap: FLOAT,
  risk_score: FLOAT,
  reliability_score: FLOAT,
  volatility: FLOAT,
  inflow_velocity: FLOAT
})
```

### Sector
```
(:Sector {
  id: STRING,           // "FRAUD_AML"
  name: STRING,         // "Fraud & AML"
  avg_price: FLOAT,
  total_market_cap: FLOAT,
  shock_sensitivity: FLOAT
})
```

### ShockEvent
```
(:ShockEvent {
  id: STRING,           // "shock_001"
  type: STRING,         // "REGULATION" | "CYBER" | "FX_SHOCK" | "EARTHQUAKE"
  severity: FLOAT,      // 0.0 - 1.0
  description: STRING,
  timestamp: DATETIME
})
```

## Edge Types

### (User)-[:ALLOCATES]->(CapitalPool)
```
[:ALLOCATES {
  amount: FLOAT,
  timestamp: DATETIME,
  action: STRING        // "buy" | "sell"
}]
```

### (CapitalPool)-[:BACKS]->(Agent)
```
[:BACKS {
  amount: FLOAT,
  weight: FLOAT,        // fraction of pool allocated to this agent
  timestamp: DATETIME
}]
```

### (Agent)-[:IN_SECTOR]->(Sector)
```
[:IN_SECTOR]
// No properties needed, static relationship
```

### (ShockEvent)-[:IMPACTS]->(Sector)
```
[:IMPACTS {
  severity: FLOAT,
  direction: FLOAT      // +1 or -1 (benefit or harm)
}]
```

### (ShockEvent)-[:IMPACTS]->(Agent)
```
[:IMPACTS {
  severity: FLOAT,
  price_delta: FLOAT    // actual price change caused
}]
```

## Seed Data Counts

| Node Type | Count | Notes |
|-----------|-------|-------|
| User | 20-50 | Simulated |
| CapitalPool | 8-12 | Each user in 1-3 pools |
| Agent | 8 | See MARKET_MODEL.md roster |
| Sector | 3 | FRAUD_AML, COMPLIANCE, GEO_OSINT |
| ShockEvent | 0 initially | Created during demo |

---

## Key Cypher Queries (5)

### 1. Top Agents by Capital Inflow (Centrality)

Find which agents attract the most capital across all pools.

```cypher
MATCH (cp:CapitalPool)-[b:BACKS]->(a:Agent)
WITH a, SUM(b.amount) AS total_inflow, COUNT(cp) AS pool_count
RETURN a.name, a.sector, total_inflow, pool_count, a.price
ORDER BY total_inflow DESC
LIMIT 5
```

### 2. Concentration Risk (Herfindahl per Agent)

Detect if one pool dominates an agent's backing (manipulation signal).

```cypher
MATCH (cp:CapitalPool)-[b:BACKS]->(a:Agent)
WITH a, SUM(b.amount) AS total,
     COLLECT({pool: cp.id, amount: b.amount}) AS pools
WITH a, total, pools,
     REDUCE(hhi = 0.0, p IN pools | hhi + (p.amount/total)^2) AS herfindahl
WHERE herfindahl > 0.4
RETURN a.name, a.sector, herfindahl, total
ORDER BY herfindahl DESC
```

### 3. Contagion Path: Shock -> Sector -> Agents -> Pools -> Users

Trace who is exposed when a shock hits a sector.

```cypher
MATCH (s:ShockEvent {id: $shock_id})-[:IMPACTS]->(sec:Sector)
      <-[:IN_SECTOR]-(a:Agent)
      <-[b:BACKS]-(cp:CapitalPool)
      <-[al:ALLOCATES]-(u:User)
RETURN s.type AS shock, sec.name AS sector,
       a.name AS agent, a.price AS price,
       cp.name AS pool, al.amount AS user_exposure,
       u.name AS user, u.risk_profile
ORDER BY al.amount DESC
```

### 4. Capital Flow Between Sectors (Cross-Sector Exposure)

Find pools that span multiple sectors (diversified vs concentrated).

```cypher
MATCH (cp:CapitalPool)-[b:BACKS]->(a:Agent)-[:IN_SECTOR]->(s:Sector)
WITH cp, COLLECT(DISTINCT s.id) AS sectors, SUM(b.amount) AS total,
     COLLECT({sector: s.id, amount: b.amount}) AS allocations
WHERE SIZE(sectors) > 1
RETURN cp.name, sectors, total, allocations
ORDER BY total DESC
```

### 5. Most Impacted Users After a Shock

Rank users by total exposure to shocked agents.

```cypher
MATCH (shock:ShockEvent {id: $shock_id})-[i:IMPACTS]->(a:Agent)
      <-[b:BACKS]-(cp:CapitalPool)
      <-[al:ALLOCATES]-(u:User)
WITH u, SUM(al.amount * ABS(i.price_delta) / a.price) AS estimated_loss
RETURN u.name, u.risk_profile, estimated_loss
ORDER BY estimated_loss DESC
LIMIT 10
```

---

## Graph Visualization Strategy

For the Neo4j Browser / Bloom visualization in the demo:

1. **Default view**: Show all nodes. Color by type:
   - Users = blue
   - Pools = green
   - Agents = orange (size by market_cap)
   - Sectors = purple
   - Shocks = red

2. **On shock injection**: Highlight the contagion path (Query #3) in red. Animate edge thickness by flow amount.

3. **On "concentration" view**: Size agent nodes by HHI score. Red border = concentration warning.

We can use Neo4j Browser's built-in visualization or embed Neovis.js in the CopilotKit UI for an inline graph view.
