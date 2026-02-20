import math
import random
import time
import uuid
import asyncio
import logging
from typing import Callable, Awaitable

from .models import AgentFundamentals, MarketState, ShockEvent, ShockType, Sector
from .seed_data import get_seed_agents

logger = logging.getLogger(__name__)

# ── Pricing parameters (see docs/MARKET_MODEL.md) ────────────────────────────
ALPHA = 0.15   # inflow sensitivity
BETA  = 0.10   # performance sensitivity
GAMMA = 0.12   # risk penalty
NOISE_STD = 0.005
PRICE_FLOOR = 1.0

# Inflow decay per tick (approaches 0 if no new activity)
INFLOW_DECAY = 0.95


class MarketEngine:
    """
    Core market simulation engine.

    Usage:
        engine = MarketEngine()
        engine.start()           # starts background tick loop
        engine.inject_shock(ShockType.REGULATION, severity=0.7)
        snapshot = engine.get_snapshot()
    """

    def __init__(self, tick_interval_ms: int = 2000):
        self.state = MarketState(agents=get_seed_agents())
        self.tick_interval_s = tick_interval_ms / 1000.0
        self._prev_fundamentals: dict[str, dict] = {}
        self._tick_callbacks: list[Callable[[MarketState], Awaitable[None]]] = []
        self._running = False
        self._task: asyncio.Task | None = None

        # Save initial fundamentals baseline
        self._snapshot_prev_fundamentals()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the async tick loop (call from FastAPI startup)."""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._tick_loop())
            logger.info("MarketEngine started")

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("MarketEngine stopped")

    def on_tick(self, callback: Callable[[MarketState], Awaitable[None]]) -> None:
        """Register a callback that fires after each market tick."""
        self._tick_callbacks.append(callback)

    # ── Public API ────────────────────────────────────────────────────────────

    def inject_shock(
        self,
        shock_type: ShockType,
        severity: float | None = None,
        description: str | None = None,
        source: str = "manual",
    ) -> ShockEvent:
        """Create and register a new shock event."""
        if severity is None:
            severity = 0.65   # sensible default for manual injection
        severity = max(0.0, min(1.0, severity))

        shock = ShockEvent(
            shock_id=str(uuid.uuid4())[:8],
            shock_type=shock_type,
            severity=severity,
            description=description or self._default_description(shock_type),
            source=source,
        )
        self.state.active_shocks.append(shock)
        logger.info(f"Shock injected: {shock_type.value} severity={severity:.2f}")
        return shock

    def get_snapshot(self) -> dict:
        return self.state.to_snapshot()

    def get_agents(self) -> list[dict]:
        return [a.to_dict() for a in self.state.agents.values()]

    def simulate_buy(self, agent_id: str, amount: float) -> None:
        """Simulate a capital inflow event for an agent."""
        agent = self.state.agents.get(agent_id)
        if agent:
            delta = amount / max(agent.total_backing, 1.0)
            agent.inflow_velocity = min(1.0, agent.inflow_velocity + delta)
            agent.total_backing += amount

    def simulate_sell(self, agent_id: str, amount: float) -> None:
        """Simulate a capital outflow event for an agent."""
        agent = self.state.agents.get(agent_id)
        if agent:
            delta = amount / max(agent.total_backing, 1.0)
            agent.inflow_velocity = max(-1.0, agent.inflow_velocity - delta)
            agent.total_backing = max(1.0, agent.total_backing - amount)

    # ── Internal tick logic ───────────────────────────────────────────────────

    async def _tick_loop(self) -> None:
        while self._running:
            try:
                self._tick()
                for cb in self._tick_callbacks:
                    await cb(self.state)
            except Exception as e:
                logger.error(f"Tick error: {e}", exc_info=True)
            await asyncio.sleep(self.tick_interval_s)

    def _tick(self) -> None:
        """One market tick: update all agent prices, decay shocks, recompute derived metrics."""
        from services.shock_engine.sector_betas import get_beta, MAX_TICK_IMPACT, DECAY_SCHEDULE

        # Collect shock impacts per agent
        shock_impacts: dict[str, float] = {aid: 0.0 for aid in self.state.agents}

        for shock in self.state.active_shocks:
            tick_index = 4 - shock.ticks_remaining          # 0,1,2,3
            decay = DECAY_SCHEDULE[min(tick_index, 3)]

            for agent in self.state.agents.values():
                beta = get_beta(shock.shock_type, agent.sector)
                raw_impact = shock.severity * beta * decay
                clamped = max(-MAX_TICK_IMPACT, min(MAX_TICK_IMPACT, raw_impact))
                shock_impacts[agent.agent_id] += clamped

        # Decay shocks
        for shock in self.state.active_shocks:
            shock.ticks_remaining -= 1
        self.state.active_shocks = [s for s in self.state.active_shocks if s.ticks_remaining > 0]

        # Update each agent
        for agent in self.state.agents.values():
            self._update_agent(agent, shock_impacts[agent.agent_id])

        # Recompute market-level metrics
        self.state.total_market_cap = sum(a.market_cap for a in self.state.agents.values())
        self.state.cascade_probability = self._compute_cascade_probability()
        self.state.tick_number += 1

        self._snapshot_prev_fundamentals()

    def _update_agent(self, agent: AgentFundamentals, shock_impact: float) -> None:
        prev = self._prev_fundamentals.get(agent.agent_id, {})
        prev_perf = prev.get("performance_score", agent.performance_score)
        prev_risk = prev.get("risk_score", agent.risk_score)

        performance_delta = agent.performance_score - prev_perf
        risk_delta = agent.risk_score - prev_risk
        noise = random.gauss(0, NOISE_STD)

        delta = (
            ALPHA * agent.inflow_velocity
            + BETA  * performance_delta
            - GAMMA * risk_delta
            + shock_impact
            + noise
        )

        new_price = agent.price * (1 + delta)
        new_price = max(PRICE_FLOOR, new_price)

        # Update price history (rolling 20)
        agent.price_history.append(new_price)
        if len(agent.price_history) > 20:
            agent.price_history.pop(0)

        agent.price = new_price
        agent.market_cap = new_price * agent.total_backing

        # Compute volatility as std dev of last 20 log-returns
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

        # Decay inflow velocity
        agent.inflow_velocity *= INFLOW_DECAY

        # Simulate passive user behavior: mild herding toward best performer
        self._simulate_passive_flows(agent)

    def _simulate_passive_flows(self, agent: AgentFundamentals) -> None:
        """Small random user allocations to keep the market alive."""
        if random.random() < 0.15:  # 15% chance each tick
            direction = 1 if agent.price_change_pct > 0 else -1
            amount = random.uniform(10, 80)
            if direction > 0:
                self.simulate_buy(agent.agent_id, amount)
            else:
                self.simulate_sell(agent.agent_id, amount * 0.5)

    def _compute_cascade_probability(self) -> float:
        """
        Simple cascade probability heuristic:
        High volatility + concentrated inflows across correlated agents → risk.
        Returns 0.0–1.0.
        """
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
