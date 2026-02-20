import math
import random
import time
import uuid
import os
import asyncio
import logging
from typing import Callable, Awaitable

from .models import AgentFundamentals, MarketState, ShockEvent, ShockType, Sector
from .seed_data import get_seed_agents

logger = logging.getLogger(__name__)

ALPHA = 0.15
BETA  = 0.10
GAMMA = 0.12
NOISE_STD = 0.005
PRICE_FLOOR = 1.0
INFLOW_DECAY = 0.95

DEMO_MODE = os.environ.get("DEMO_MODE", "").lower() in ("true", "1", "yes")
DEMO_SEED = 42

DEMO_SHOCK_SEVERITIES = {
    ShockType.REGULATION: 0.70,
    ShockType.CYBER:      0.60,
    ShockType.FX_SHOCK:   0.50,
    ShockType.EARTHQUAKE: 0.55,
    ShockType.SANCTIONS:  0.65,
}


class MarketEngine:
    def __init__(self, tick_interval_ms: int = 2000):
        self.state = MarketState(agents=get_seed_agents())
        self.tick_interval_s = tick_interval_ms / 1000.0
        self._prev_fundamentals: dict[str, dict] = {}
        self._tick_callbacks: list[Callable[[MarketState], Awaitable[None]]] = []
        self._running = False
        self._task: asyncio.Task | None = None

        self.peak_market_cap: float = 0.0
        self.drawdown_pct: float = 0.0
        self.last_tick_latency_ms: float = 0.0

        self._rng = random.Random(DEMO_SEED if DEMO_MODE else None)

        self._snapshot_prev_fundamentals()

        if DEMO_MODE:
            logger.info("MarketEngine running in DEMO_MODE (seeded RNG, fixed severities)")

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._tick_loop())
            logger.info("MarketEngine started (tick=%.1fs)", self.tick_interval_s)

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("MarketEngine stopped")

    def on_tick(self, callback: Callable[[MarketState], Awaitable[None]]) -> None:
        self._tick_callbacks.append(callback)

    def inject_shock(
        self,
        shock_type: ShockType,
        severity: float | None = None,
        description: str | None = None,
        source: str = "manual",
    ) -> ShockEvent:
        if severity is None:
            severity = DEMO_SHOCK_SEVERITIES.get(shock_type, 0.65) if DEMO_MODE else 0.65
        severity = max(0.0, min(1.0, severity))

        shock = ShockEvent(
            shock_id=str(uuid.uuid4())[:8],
            shock_type=shock_type,
            severity=severity,
            description=description or self._default_description(shock_type),
            source=source,
        )
        self.state.active_shocks.append(shock)
        logger.info("Shock injected: %s severity=%.2f", shock_type.value, severity)
        return shock

    def get_snapshot(self) -> dict:
        snapshot = self.state.to_snapshot()
        snapshot["drawdown_pct"] = round(self.drawdown_pct, 4)
        snapshot["peak_market_cap"] = round(self.peak_market_cap, 2)
        return snapshot

    def get_agents(self) -> list[dict]:
        return [a.to_dict() for a in self.state.agents.values()]

    def simulate_buy(self, agent_id: str, amount: float) -> None:
        agent = self.state.agents.get(agent_id)
        if agent:
            delta = amount / max(agent.total_backing, 1.0)
            agent.inflow_velocity = min(1.0, agent.inflow_velocity + delta)
            agent.total_backing += amount

    def simulate_sell(self, agent_id: str, amount: float) -> None:
        agent = self.state.agents.get(agent_id)
        if agent:
            delta = amount / max(agent.total_backing, 1.0)
            agent.inflow_velocity = max(-1.0, agent.inflow_velocity - delta)
            agent.total_backing = max(1.0, agent.total_backing - amount)

    async def _tick_loop(self) -> None:
        while self._running:
            try:
                tick_start = time.time()
                self._tick()
                self.last_tick_latency_ms = (time.time() - tick_start) * 1000

                for cb in self._tick_callbacks:
                    await cb(self.state)
            except Exception as e:
                logger.error("Tick error: %s", e, exc_info=True)
            await asyncio.sleep(self.tick_interval_s)

    def _tick(self) -> None:
        from backend.services.shock_engine.sector_betas import get_beta, MAX_TICK_IMPACT, DECAY_SCHEDULE

        shock_impacts: dict[str, float] = {aid: 0.0 for aid in self.state.agents}

        for shock in self.state.active_shocks:
            tick_index = 4 - shock.ticks_remaining
            decay = DECAY_SCHEDULE[min(tick_index, 3)]

            for agent in self.state.agents.values():
                beta = get_beta(shock.shock_type, agent.sector)
                raw_impact = shock.severity * beta * decay
                clamped = max(-MAX_TICK_IMPACT, min(MAX_TICK_IMPACT, raw_impact))
                shock_impacts[agent.agent_id] += clamped

        for shock in self.state.active_shocks:
            shock.ticks_remaining -= 1
        self.state.active_shocks = [s for s in self.state.active_shocks if s.ticks_remaining > 0]

        for agent in self.state.agents.values():
            self._update_agent(agent, shock_impacts[agent.agent_id])

        self.state.total_market_cap = sum(a.market_cap for a in self.state.agents.values())
        self.state.cascade_probability = self._compute_cascade_probability()
        self.state.tick_number += 1

        if self.state.total_market_cap > self.peak_market_cap:
            self.peak_market_cap = self.state.total_market_cap
        if self.peak_market_cap > 0:
            self.drawdown_pct = ((self.state.total_market_cap - self.peak_market_cap) / self.peak_market_cap) * 100

        self._snapshot_prev_fundamentals()

    def _update_agent(self, agent: AgentFundamentals, shock_impact: float) -> None:
        prev = self._prev_fundamentals.get(agent.agent_id, {})
        prev_perf = prev.get("performance_score", agent.performance_score)
        prev_risk = prev.get("risk_score", agent.risk_score)

        performance_delta = agent.performance_score - prev_perf
        risk_delta = agent.risk_score - prev_risk
        noise = self._rng.gauss(0, NOISE_STD)

        delta = (
            ALPHA * agent.inflow_velocity
            + BETA  * performance_delta
            - GAMMA * risk_delta
            + shock_impact
            + noise
        )

        new_price = agent.price * (1 + delta)
        new_price = max(PRICE_FLOOR, new_price)

        agent.price_history.append(new_price)
        if len(agent.price_history) > 20:
            agent.price_history.pop(0)

        agent.price = new_price
        agent.market_cap = new_price * agent.total_backing

        if len(agent.price_history) >= 2:
            returns = [
                math.log(agent.price_history[i] / agent.price_history[i - 1])
                for i in range(1, len(agent.price_history))
                if agent.price_history[i - 1] > 0
            ]
            if returns:
                mean = sum(returns) / len(returns)
                variance = sum((r - mean) ** 2 for r in returns) / len(returns)
                agent.volatility = math.sqrt(variance)

        agent.inflow_velocity *= INFLOW_DECAY
        self._simulate_passive_flows(agent)

    def _simulate_passive_flows(self, agent: AgentFundamentals) -> None:
        if self._rng.random() < 0.15:
            direction = 1 if agent.price_change_pct > 0 else -1
            amount = self._rng.uniform(10, 80)
            if direction > 0:
                self.simulate_buy(agent.agent_id, amount)
            else:
                self.simulate_sell(agent.agent_id, amount * 0.5)

    def _compute_cascade_probability(self) -> float:
        avg_volatility = sum(a.volatility for a in self.state.agents.values()) / max(len(self.state.agents), 1)
        active_shock_severity = sum(s.severity for s in self.state.active_shocks)
        cascade = min(1.0, (avg_volatility * 10) + (active_shock_severity * 0.3))
        return round(cascade, 4)

    def _snapshot_prev_fundamentals(self) -> None:
        self._prev_fundamentals = {
            aid: {
                "performance_score": a.performance_score,
                "risk_score": a.risk_score,
            }
            for aid, a in self.state.agents.items()
        }

    def _default_description(self, shock_type: ShockType) -> str:
        descriptions = {
            ShockType.REGULATION: "Regulatory crackdown on AI systems announced",
            ShockType.CYBER:       "Large-scale cyber attack detected across financial networks",
            ShockType.FX_SHOCK:    "Significant FX volatility spike in major currency pair",
            ShockType.EARTHQUAKE:  "Major earthquake near financial infrastructure hub",
            ShockType.SANCTIONS:   "New sanctions package targeting tech sector announced",
        }
        return descriptions.get(shock_type, "Market shock event")
