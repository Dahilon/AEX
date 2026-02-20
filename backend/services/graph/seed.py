"""
Seed the Neo4j graph with demo data.

Run once before the demo:
    python -m backend.services.graph.seed

Creates: Users, CapitalPools, Agents, Sectors, and all edges.
"""

import uuid
import random
import logging
from backend.services.graph.service import GraphService
from backend.services.market_engine.seed_data import SEED_AGENTS
from backend.services.graph import queries as Q

logger = logging.getLogger(__name__)

SECTORS = [
    {"id": "FRAUD_AML",  "name": "Fraud & AML"},
    {"id": "COMPLIANCE", "name": "Compliance"},
    {"id": "GEO_OSINT",  "name": "Geo Intelligence & OSINT"},
]

USER_PROFILES = ["aggressive", "moderate", "conservative"]
USER_NAMES = [
    "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace",
    "Hank", "Iris", "Jack", "Karen", "Leo", "Mia", "Nick", "Olivia",
    "Pete", "Quinn", "Rachel", "Sam", "Tina",
]

POOL_STRATEGIES = ["sector_balanced", "high_risk", "safe_haven", "growth"]
POOL_NAMES = [
    "Alpha Fund", "Beta Capital", "Gamma Pool",
    "Delta Reserve", "Epsilon Ventures", "Zeta Allocation",
    "Eta Growth", "Theta Safe Haven", "Iota Balanced",
]


def seed_all() -> None:
    svc = GraphService()
    svc.connect()

    logger.info("Seeding sectors...")
    _seed_sectors(svc)

    logger.info("Seeding agents...")
    _seed_agents(svc)

    logger.info("Seeding users...")
    users = _seed_users(svc)

    logger.info("Seeding capital pools...")
    pools = _seed_pools(svc)

    logger.info("Creating user → pool edges...")
    _seed_allocates(svc, users, pools)

    logger.info("Creating pool → agent edges...")
    _seed_backs(svc, pools)

    logger.info("Graph seeding complete!")
    svc.close()


def _seed_sectors(svc: GraphService) -> None:
    with svc._session() as session:
        for s in SECTORS:
            session.run(Q.CREATE_SECTOR, id=s["id"], name=s["name"])


def _seed_agents(svc: GraphService) -> None:
    with svc._session() as session:
        for agent in SEED_AGENTS:
            session.run(
                Q.CREATE_AGENT,
                id=agent.agent_id,
                name=agent.name,
                sector=agent.sector.value,
                price=agent.price,
                market_cap=agent.market_cap,
                risk_score=agent.risk_score,
                reliability_score=agent.reliability_score,
                volatility=agent.volatility,
                inflow_velocity=agent.inflow_velocity,
            )
            session.run(
                Q.CREATE_AGENT_IN_SECTOR,
                agent_id=agent.agent_id,
                sector_id=agent.sector.value,
            )


def _seed_users(svc: GraphService) -> list[dict]:
    users = []
    with svc._session() as session:
        for i, name in enumerate(USER_NAMES):
            uid = f"user_{i+1:03d}"
            profile = random.choice(USER_PROFILES)
            allocated = random.uniform(500, 10000)
            session.run(
                Q.CREATE_USER,
                id=uid, name=name,
                risk_profile=profile,
                total_allocated=allocated,
            )
            users.append({"id": uid, "name": name, "risk_profile": profile, "allocated": allocated})
    return users


def _seed_pools(svc: GraphService) -> list[dict]:
    pools = []
    with svc._session() as session:
        for i, name in enumerate(POOL_NAMES):
            pid = f"pool_{i+1:03d}"
            strategy = random.choice(POOL_STRATEGIES)
            value = random.uniform(2000, 20000)
            session.run(
                Q.CREATE_CAPITAL_POOL,
                id=pid, name=name,
                total_value=value,
                strategy=strategy,
            )
            pools.append({"id": pid, "name": name, "strategy": strategy, "value": value})
    return pools


def _seed_allocates(svc: GraphService, users: list[dict], pools: list[dict]) -> None:
    """Each user allocates to 1-3 pools."""
    with svc._session() as session:
        for user in users:
            assigned = random.sample(pools, k=random.randint(1, 3))
            for pool in assigned:
                amount = user["allocated"] / len(assigned)
                session.run(
                    Q.CREATE_ALLOCATES_EDGE,
                    user_id=user["id"],
                    pool_id=pool["id"],
                    amount=round(amount, 2),
                )


def _seed_backs(svc: GraphService, pools: list[dict]) -> None:
    """Each pool backs 2-4 agents with weights summing to 1."""
    agent_ids = [a.agent_id for a in SEED_AGENTS]
    with svc._session() as session:
        for pool in pools:
            backed = random.sample(agent_ids, k=random.randint(2, 4))
            weights = _random_weights(len(backed))
            for agent_id, weight in zip(backed, weights):
                amount = pool["value"] * weight
                session.run(
                    Q.CREATE_BACKS_EDGE,
                    pool_id=pool["id"],
                    agent_id=agent_id,
                    amount=round(amount, 2),
                    weight=round(weight, 4),
                )


def _random_weights(n: int) -> list[float]:
    raw = [random.random() for _ in range(n)]
    total = sum(raw)
    return [r / total for r in raw]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_all()
