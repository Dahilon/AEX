"""
TestSprite test runner routes.
"""

import logging
import time
from fastapi import APIRouter, Request
from pydantic import BaseModel

from backend.services.observability.correlation import new_run_id
from backend.services.observability.metrics import emit_test_metrics
from backend.services.observability.events import emit_test_event

logger = logging.getLogger(__name__)
router = APIRouter()


class RunTestsRequest(BaseModel):
    test_name: str = "all"


@router.post("/run")
async def run_tests(body: RunTestsRequest, request: Request) -> dict:
    run_id = new_run_id("test")
    engine = request.app.state.engine
    results = []

    tests_to_run = ["inflow_price_rule", "shock_sector_rule"] if body.test_name == "all" else [body.test_name]

    for test in tests_to_run:
        if test == "inflow_price_rule":
            result = await _test_inflow_price_rule(engine)
        elif test == "shock_sector_rule":
            result = await _test_shock_sector_rule(engine)
        else:
            result = {"test_name": test, "status": "ERROR", "duration_ms": 0, "details": {}, "error": f"Unknown test: {test}"}
        results.append(result)
        emit_test_metrics(result["test_name"], result["status"] == "PASS", result.get("duration_ms", 0))

    passed = sum(1 for r in results if r["status"] == "PASS")
    summary = f"{passed}/{len(results)} PASSED"

    emit_test_event(summary, results, run_id)

    return {"results": results, "summary": summary, "run_id": run_id}


async def _test_inflow_price_rule(engine) -> dict:
    start = time.time()
    test_agent_id = "fraudguard_v3"
    agent = engine.state.agents.get(test_agent_id)
    if not agent:
        return {"test_name": "inflow_price_rule", "status": "ERROR", "duration_ms": 0, "details": {}, "error": "Test agent not found"}

    price_before = agent.price
    inflow_before = agent.inflow_velocity

    for _ in range(5):
        engine.simulate_buy(test_agent_id, 1000.0)
    for _ in range(3):
        engine._tick()

    price_after = agent.price
    price_change_pct = ((price_after - price_before) / price_before) * 100
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
            "inflow_after": round(agent.inflow_velocity, 4),
            "threshold_pct": 1.0,
        },
    }


async def _test_shock_sector_rule(engine) -> dict:
    from backend.services.market_engine.models import ShockType, Sector

    start = time.time()

    def sector_avg_price(sector: Sector) -> float:
        agents = [a for a in engine.state.agents.values() if a.sector == sector]
        return sum(a.price for a in agents) / len(agents) if agents else 0.0

    compliance_before = sector_avg_price(Sector.COMPLIANCE)
    fraud_aml_before = sector_avg_price(Sector.FRAUD_AML)

    engine.inject_shock(ShockType.REGULATION, severity=0.7, source="test")
    for _ in range(5):
        engine._tick()

    compliance_after = sector_avg_price(Sector.COMPLIANCE)
    fraud_aml_after = sector_avg_price(Sector.FRAUD_AML)

    compliance_change = ((compliance_after - compliance_before) / compliance_before) * 100
    fraud_aml_change = ((fraud_aml_after - fraud_aml_before) / fraud_aml_before) * 100
    spread = compliance_change - fraud_aml_change

    passed = compliance_change > 0 and fraud_aml_change < 0 and spread >= 3.0

    return {
        "test_name": "shock_sector_rule",
        "status": "PASS" if passed else "FAIL",
        "duration_ms": round((time.time() - start) * 1000),
        "details": {
            "compliance_avg_change_pct": round(compliance_change, 2),
            "fraud_aml_avg_change_pct": round(fraud_aml_change, 2),
            "spread_pct": round(spread, 2),
            "threshold_spread_pct": 3.0,
        },
    }
