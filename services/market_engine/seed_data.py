from .models import AgentFundamentals, Sector

# ── 8 Agents seeded at demo-realistic values ─────────────────────────────────
# See docs/MARKET_MODEL.md for full rationale.

SEED_AGENTS: list[AgentFundamentals] = [
    # ── FRAUD & AML ──────────────────────────────────────────────────────────
    AgentFundamentals(
        agent_id="fraudguard_v3",
        name="FraudGuard-v3",
        sector=Sector.FRAUD_AML,
        usage_score=0.85,
        performance_score=0.78,
        reliability_score=0.92,
        risk_score=0.35,
        inflow_velocity=0.08,
        total_backing=5000.0,
        price=142.50,
    ),
    AgentFundamentals(
        agent_id="amlscan_pro",
        name="AMLScan-Pro",
        sector=Sector.FRAUD_AML,
        usage_score=0.72,
        performance_score=0.81,
        reliability_score=0.88,
        risk_score=0.42,
        inflow_velocity=0.03,
        total_backing=3800.0,
        price=98.30,
    ),
    AgentFundamentals(
        agent_id="txnmonitor",
        name="TxnMonitor",
        sector=Sector.FRAUD_AML,
        usage_score=0.65,
        performance_score=0.70,
        reliability_score=0.95,
        risk_score=0.28,
        inflow_velocity=-0.02,
        total_backing=2900.0,
        price=76.00,
    ),
    # ── COMPLIANCE ───────────────────────────────────────────────────────────
    AgentFundamentals(
        agent_id="complibot_eu",
        name="CompliBot-EU",
        sector=Sector.COMPLIANCE,
        usage_score=0.90,
        performance_score=0.85,
        reliability_score=0.90,
        risk_score=0.20,
        inflow_velocity=0.15,
        total_backing=6500.0,
        price=210.00,
    ),
    AgentFundamentals(
        agent_id="regwatch_us",
        name="RegWatch-US",
        sector=Sector.COMPLIANCE,
        usage_score=0.78,
        performance_score=0.82,
        reliability_score=0.87,
        risk_score=0.25,
        inflow_velocity=0.06,
        total_backing=4200.0,
        price=165.40,
    ),
    AgentFundamentals(
        agent_id="sanctionscreen",
        name="SanctionScreen",
        sector=Sector.COMPLIANCE,
        usage_score=0.60,
        performance_score=0.75,
        reliability_score=0.93,
        risk_score=0.30,
        inflow_velocity=0.01,
        total_backing=2100.0,
        price=88.00,
    ),
    # ── GEO / OSINT ──────────────────────────────────────────────────────────
    AgentFundamentals(
        agent_id="geointel_live",
        name="GeoIntel-Live",
        sector=Sector.GEO_OSINT,
        usage_score=0.70,
        performance_score=0.68,
        reliability_score=0.80,
        risk_score=0.55,
        inflow_velocity=-0.05,
        total_backing=1800.0,
        price=55.20,
    ),
    AgentFundamentals(
        agent_id="threatmapper",
        name="ThreatMapper",
        sector=Sector.GEO_OSINT,
        usage_score=0.55,
        performance_score=0.62,
        reliability_score=0.75,
        risk_score=0.60,
        inflow_velocity=-0.08,
        total_backing=1400.0,
        price=42.80,
    ),
]


def get_seed_agents() -> dict[str, AgentFundamentals]:
    """Return a fresh dict of agent_id -> AgentFundamentals."""
    return {a.agent_id: a for a in SEED_AGENTS}
