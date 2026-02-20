"""
TestSprite test runner routes.
See docs/TESTING.md for full test specs.
"""

import logging
import time
import uuid
from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()


class RunTestsRequest(BaseModel):
    test_name: str = "all"  # "all" | "inflow_price_rule" | "shock_sector_rule"


@router.post("/run")
async def run_tests(body: RunTestsRequest, request: Request) -> dict:
    """
    Run TestSprite tests against the market engine.
    Returns pass/fail results with details.
    """
    engine = request.app.state.engine
    results = []

    tests_to_run = []
    if body.test_name == "all":
        tests_to_run = ["inflow_price_rule", "shock_sector_rule"]
    else:
        tests_to_run = [body.test_name]

    for test in tests_to_run:
        if test == "inflow_price_rule":
            result = await _test_inflow_price_rule(engine)
        elif test == "shock_sector_rule":
            result = await _test_shock_sector_rule(engine)
        else:
            result = {
                "test_name": test,
                "status": "ERROR",
                "duration_ms": 0,
                "details": {},
                "error": f"Unknown test: {test}",
            }
        results.append(result)

    passed = sum(1 for r in results if r["status"] == "PASS")
    return {
        "results": results,
        "summary": f"{passed}/{len(results)} PASSED",
    }


async def _test_inflow_price_rule(engine) -> dict:
    """
    Test: capital inflow must increase agent price.
    Spec: simulate 5 buys → run 3 ticks → price must be >= 1% higher.
    """
    start = time.time()
    test_agent_id = "fraudguard_v3"

    agent = engine.state.agents.get(test_agent_id)
    if not agent:
        return {"test_name": "inflow_price_rule", "status": "ERROR",
                "duration_ms": 0, "details": {}, "error": "Test agent not found"}

    price_before = agent.price
    inflow_before = agent.inflow_velocity

    # Simulate 5 buy events
    for _ in range(5):
        engine.simulate_buy(test_agent_id, 1000.0)

    # Run 3 market ticks manually
    for _ in range(3):
        engine._tick()

    price_after = agent.price
    price_change_pct = ((price_after - price_before) / price_before) * 100
    inflow_after = agent.inflow_velocity

    passed = price_after > price_before and price_change_pct >= 1.0

    return {
        "test_name": "inflow_price_rule",
        "status": "PASS" if passed else "FAIL",
        "duration_ms": round((time.time() - start) * 1000),
        "details": {
            "price_before": round(price_before, 2),
            "price_after": round(price_after, 2),
            "price_change_pct": round(price_change_pct, 2),
            "inflow_before": round(inflow_before, 4),
            "inflow_after": round(inflow_after, 4),
            "threshold_pct": 1.0,
        },
    }


async def _test_shock_sector_rule(engine) -> dict:
    """
    Test: REGULATION shock → Compliance outperforms Fraud/AML.
    Spec: inject REGULATION 0.7 → run 5 ticks → Compliance avg > 0%, Fraud/AML avg < 0%, spread >= 3%.
    """
    import asyncio
    from backend.services.market_engine.models import ShockType, Sector

    start = time.time()

    # Snapshot prices before
    def sector_avg_price(sector: Sector) -> float:
        agents = [a for a in engine.state.agents.values() if a.sector == sector]
        return sum(a.price for a in agents) / len(agents) if agents else 0.0

    compliance_price_before = sector_avg_price(Sector.COMPLIANCE)
    fraud_aml_price_before = sector_avg_price(Sector.FRAUD_AML)

    # Inject regulation shock
    engine.inject_shock(ShockType.REGULATION, severity=0.7, source="test")

    # Run 5 ticks
    for _ in range(5):
        engine._tick()

    compliance_price_after = sector_avg_price(Sector.COMPLIANCE)
    fraud_aml_price_after = sector_avg_price(Sector.FRAUD_AML)

    compliance_change = ((compliance_price_after - compliance_price_before) / compliance_price_before) * 100
    fraud_aml_change = ((fraud_aml_price_after - fraud_aml_price_before) / fraud_aml_price_before) * 100
    spread = compliance_change - fraud_aml_change

    passed = (
        compliance_change > 0
        and fraud_aml_change < 0
        and spread >= 3.0
    )

    return {
        "test_name": "shock_sector_rule",
        "status": "PASS" if passed else "FAIL",
        "duration_ms": round((time.time() - start) * 1000),
        "details": {
            "compliance_avg_change_pct": round(compliance_change, 2),
            "fraud_aml_avg_change_pct": round(fraud_aml_change, 2),
            "spread_pct": round(spread, 2),
            "threshold_spread_pct": 3.0,
            "shock_type": "REGULATION",
            "shock_severity": 0.7,
        },
    }
