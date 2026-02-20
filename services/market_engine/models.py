from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import time


class Sector(str, Enum):
    FRAUD_AML = "FRAUD_AML"
    COMPLIANCE = "COMPLIANCE"
    GEO_OSINT = "GEO_OSINT"


class ShockType(str, Enum):
    REGULATION = "REGULATION"
    CYBER = "CYBER"
    FX_SHOCK = "FX_SHOCK"
    EARTHQUAKE = "EARTHQUAKE"
    SANCTIONS = "SANCTIONS"


@dataclass
class AgentFundamentals:
    agent_id: str
    name: str
    sector: Sector

    # Core scores (0.0–1.0)
    usage_score: float = 0.5
    performance_score: float = 0.5
    reliability_score: float = 0.5
    risk_score: float = 0.5

    # Flow metrics
    inflow_velocity: float = 0.0       # normalized [-1, +1], decays toward 0
    total_backing: float = 1000.0      # total capital allocated

    # Price state
    price: float = 100.0
    price_history: list[float] = field(default_factory=list)  # last 20 ticks
    volatility: float = 0.02

    # Market metrics
    market_cap: float = field(init=False)

    def __post_init__(self):
        self.market_cap = self.price * self.total_backing
        if not self.price_history:
            self.price_history = [self.price] * 20

    @property
    def price_change_pct(self) -> float:
        """Percentage change from 20 ticks ago."""
        if len(self.price_history) < 2:
            return 0.0
        oldest = self.price_history[0]
        if oldest == 0:
            return 0.0
        return ((self.price - oldest) / oldest) * 100

    @property
    def inflow_direction(self) -> str:
        if self.inflow_velocity > 0.05:
            return "up"
        elif self.inflow_velocity < -0.05:
            return "down"
        return "flat"

    def to_dict(self) -> dict:
        return {
            "id": self.agent_id,
            "name": self.name,
            "sector": self.sector.value,
            "price": round(self.price, 2),
            "price_change_pct": round(self.price_change_pct, 2),
            "market_cap": round(self.market_cap, 2),
            "usage_score": self.usage_score,
            "performance_score": self.performance_score,
            "reliability_score": self.reliability_score,
            "risk_score": self.risk_score,
            "inflow_velocity": round(self.inflow_velocity, 4),
            "inflow_direction": self.inflow_direction,
            "volatility": round(self.volatility, 4),
            "total_backing": self.total_backing,
        }


@dataclass
class ShockEvent:
    shock_id: str
    shock_type: ShockType
    severity: float          # 0.0–1.0
    description: str
    timestamp: float = field(default_factory=time.time)
    ticks_remaining: int = 4  # shock decays over 4 ticks
    source: str = "manual"   # "manual" | "GDELT" | "USGS" | "FX"

    def to_dict(self) -> dict:
        return {
            "id": self.shock_id,
            "type": self.shock_type.value,
            "severity": self.severity,
            "description": self.description,
            "timestamp": self.timestamp,
            "ticks_remaining": self.ticks_remaining,
            "source": self.source,
        }


@dataclass
class SignalEvent:
    signal_id: str
    source: str              # "GDELT" | "USGS" | "FX"
    signal_type: str         # "NEWS" | "EARTHQUAKE" | "FX_MOVE"
    timestamp: float
    severity_hint: float     # 0.0–1.0 raw estimate from source
    metadata: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)


@dataclass
class MarketState:
    agents: dict[str, AgentFundamentals] = field(default_factory=dict)
    active_shocks: list[ShockEvent] = field(default_factory=list)
    tick_number: int = 0
    total_market_cap: float = 0.0
    cascade_probability: float = 0.0

    def to_snapshot(self) -> dict:
        return {
            "tick_number": self.tick_number,
            "total_market_cap": round(self.total_market_cap, 2),
            "cascade_probability": round(self.cascade_probability, 4),
            "active_shocks": [s.to_dict() for s in self.active_shocks],
            "agents": [a.to_dict() for a in self.agents.values()],
            "sectors": self._sector_summary(),
        }

    def _sector_summary(self) -> list[dict]:
        by_sector: dict[str, list[AgentFundamentals]] = {}
        for agent in self.agents.values():
            by_sector.setdefault(agent.sector.value, []).append(agent)

        result = []
        for sector_id, agents in by_sector.items():
            avg_change = sum(a.price_change_pct for a in agents) / len(agents)
            total_cap = sum(a.market_cap for a in agents)
            result.append({
                "id": sector_id,
                "avg_price_change_pct": round(avg_change, 2),
                "total_market_cap": round(total_cap, 2),
                "agent_count": len(agents),
            })
        return result
