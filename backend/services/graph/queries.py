"""
Cypher query templates for AEX graph operations.
See docs/GRAPH_SCHEMA.md for full explanation of each query.
"""

# Q1: Top agents by total capital inflow
TOP_INFLOW = """
MATCH (cp:CapitalPool)-[b:BACKS]->(a:Agent)
WITH a, SUM(b.amount) AS total_inflow, COUNT(cp) AS pool_count
RETURN a.id AS agent_id, a.name AS name, a.sector AS sector,
       total_inflow, pool_count, a.price AS price
ORDER BY total_inflow DESC
LIMIT $limit
"""

# Q2: Concentration risk (Herfindahl index per agent)
CONCENTRATION_RISK = """
MATCH (cp:CapitalPool)-[b:BACKS]->(a:Agent)
WITH a, SUM(b.amount) AS total,
     COLLECT({pool: cp.id, amount: b.amount}) AS pools
WITH a, total, pools,
     REDUCE(hhi = 0.0, p IN pools | hhi + (p.amount / total)^2) AS herfindahl
WHERE herfindahl > $min_hhi
RETURN a.id AS agent_id, a.name AS name, a.sector AS sector,
       herfindahl, total
ORDER BY herfindahl DESC
"""

# Q3: Contagion path — who is exposed to a shocked sector?
CONTAGION_PATH = """
MATCH (s:ShockEvent {id: $shock_id})-[:IMPACTS]->(sec:Sector)
      <-[:IN_SECTOR]-(a:Agent)
      <-[b:BACKS]-(cp:CapitalPool)
      <-[al:ALLOCATES]-(u:User)
RETURN s.type AS shock_type,
       sec.id AS sector,
       a.id AS agent_id, a.name AS agent_name, a.price AS price,
       cp.id AS pool_id, cp.name AS pool_name,
       al.amount AS exposure,
       u.id AS user_id, u.name AS user_name, u.risk_profile AS risk_profile
ORDER BY al.amount DESC
"""

# Q4: Cross-sector exposure (which pools span multiple sectors?)
CROSS_SECTOR_EXPOSURE = """
MATCH (cp:CapitalPool)-[b:BACKS]->(a:Agent)-[:IN_SECTOR]->(s:Sector)
WITH cp, COLLECT(DISTINCT s.id) AS sectors, SUM(b.amount) AS total,
     COLLECT({sector: s.id, amount: b.amount}) AS allocations
WHERE SIZE(sectors) > 1
RETURN cp.id AS pool_id, cp.name AS pool_name,
       sectors, total, allocations
ORDER BY total DESC
"""

# Q5: Most impacted users after a shock
MOST_IMPACTED_USERS = """
MATCH (shock:ShockEvent {id: $shock_id})-[i:IMPACTS]->(a:Agent)
      <-[b:BACKS]-(cp:CapitalPool)
      <-[al:ALLOCATES]-(u:User)
WITH u, SUM(al.amount * ABS(coalesce(i.price_delta, 0.0)) / CASE a.price WHEN 0 THEN 1 ELSE a.price END) AS estimated_loss
RETURN u.id AS user_id, u.name AS user_name, u.risk_profile,
       estimated_loss
ORDER BY estimated_loss DESC
LIMIT $limit
"""

# ── Seed / write queries ──────────────────────────────────────────────────────

CREATE_AGENT = """
MERGE (a:Agent {id: $id})
SET a.name = $name,
    a.sector = $sector,
    a.price = $price,
    a.market_cap = $market_cap,
    a.risk_score = $risk_score,
    a.reliability_score = $reliability_score,
    a.volatility = $volatility,
    a.inflow_velocity = $inflow_velocity
"""

CREATE_SECTOR = """
MERGE (s:Sector {id: $id})
SET s.name = $name
"""

CREATE_AGENT_IN_SECTOR = """
MATCH (a:Agent {id: $agent_id})
MATCH (s:Sector {id: $sector_id})
MERGE (a)-[:IN_SECTOR]->(s)
"""

CREATE_USER = """
MERGE (u:User {id: $id})
SET u.name = $name,
    u.risk_profile = $risk_profile,
    u.total_allocated = $total_allocated
"""

CREATE_CAPITAL_POOL = """
MERGE (cp:CapitalPool {id: $id})
SET cp.name = $name,
    cp.total_value = $total_value,
    cp.strategy = $strategy
"""

CREATE_ALLOCATES_EDGE = """
MATCH (u:User {id: $user_id})
MATCH (cp:CapitalPool {id: $pool_id})
CREATE (u)-[:ALLOCATES {amount: $amount, timestamp: datetime()}]->(cp)
"""

CREATE_BACKS_EDGE = """
MATCH (cp:CapitalPool {id: $pool_id})
MATCH (a:Agent {id: $agent_id})
MERGE (cp)-[r:BACKS]->(a)
SET r.amount = $amount,
    r.weight = $weight,
    r.timestamp = datetime()
"""

CREATE_SHOCK_NODE = """
MERGE (s:ShockEvent {id: $id})
SET s.type = $type,
    s.severity = $severity,
    s.description = $description,
    s.timestamp = datetime()
"""

CREATE_SHOCK_IMPACTS_SECTOR = """
MATCH (s:ShockEvent {id: $shock_id})
MATCH (sec:Sector {id: $sector_id})
MERGE (s)-[r:IMPACTS]->(sec)
SET r.severity = $severity, r.direction = $direction
"""

UPDATE_AGENT_PRICE = """
MATCH (a:Agent {id: $agent_id})
SET a.price = $price,
    a.market_cap = $market_cap,
    a.volatility = $volatility,
    a.inflow_velocity = $inflow_velocity
"""
