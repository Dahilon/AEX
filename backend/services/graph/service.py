"""
Neo4j graph service.

All graph interactions go through GraphService.
Uses the official neo4j Python driver with Aura connection.

Usage:
    svc = GraphService()
    svc.connect()
    svc.run_query("top_inflow", {"limit": 5})
"""

import os
import logging
from neo4j import GraphDatabase, Driver, Session

from . import queries as Q

logger = logging.getLogger(__name__)


class GraphService:
    def __init__(self):
        self._driver: Driver | None = None

    def connect(self) -> None:
        uri  = os.environ["NEO4J_URI"]
        user = os.environ["NEO4J_USER"]
        pw   = os.environ["NEO4J_PASSWORD"]
        self._driver = GraphDatabase.driver(uri, auth=(user, pw))
        self._driver.verify_connectivity()
        logger.info(f"Neo4j connected: {uri}")

    def close(self) -> None:
        if self._driver:
            self._driver.close()

    def _session(self) -> Session:
        if not self._driver:
            raise RuntimeError("GraphService not connected. Call connect() first.")
        return self._driver.session()

    # ── Named query runner ────────────────────────────────────────────────────

    def run_query(self, query_type: str, params: dict | None = None) -> list[dict]:
        """
        Execute a named query and return results as list of dicts.

        query_type options:
            "top_inflow"           → Q.TOP_INFLOW
            "concentration_risk"   → Q.CONCENTRATION_RISK
            "contagion_path"       → Q.CONTAGION_PATH
            "cross_sector_exposure"→ Q.CROSS_SECTOR_EXPOSURE
            "most_impacted_users"  → Q.MOST_IMPACTED_USERS
        """
        params = params or {}
        query_map = {
            "top_inflow":            (Q.TOP_INFLOW,             {"limit": 5}),
            "concentration_risk":    (Q.CONCENTRATION_RISK,     {"min_hhi": 0.35}),
            "contagion_path":        (Q.CONTAGION_PATH,         {}),
            "cross_sector_exposure": (Q.CROSS_SECTOR_EXPOSURE,  {}),
            "most_impacted_users":   (Q.MOST_IMPACTED_USERS,    {"limit": 10}),
        }

        if query_type not in query_map:
            raise ValueError(f"Unknown query_type: {query_type}")

        cypher, defaults = query_map[query_type]
        merged_params = {**defaults, **params}

        with self._session() as session:
            result = session.run(cypher, **merged_params)
            return [record.data() for record in result]

    # ── Write helpers ─────────────────────────────────────────────────────────

    def upsert_agent(self, agent_dict: dict) -> None:
        with self._session() as session:
            session.run(Q.CREATE_AGENT, **agent_dict)

    def update_agent_price(self, agent_id: str, price: float, market_cap: float,
                           volatility: float, inflow_velocity: float) -> None:
        with self._session() as session:
            session.run(
                Q.UPDATE_AGENT_PRICE,
                agent_id=agent_id,
                price=price,
                market_cap=market_cap,
                volatility=volatility,
                inflow_velocity=inflow_velocity,
            )

    def create_shock(self, shock_dict: dict) -> None:
        with self._session() as session:
            session.run(
                Q.CREATE_SHOCK_NODE,
                id=shock_dict["id"],
                type=shock_dict["type"],
                severity=shock_dict["severity"],
                description=shock_dict["description"],
            )

    def link_shock_to_sectors(self, shock_id: str, sector_impacts: list[dict]) -> None:
        """sector_impacts: [{"sector_id": "COMPLIANCE", "severity": 0.7, "direction": 1}]"""
        with self._session() as session:
            for impact in sector_impacts:
                session.run(
                    Q.CREATE_SHOCK_IMPACTS_SECTOR,
                    shock_id=shock_id,
                    sector_id=impact["sector_id"],
                    severity=impact["severity"],
                    direction=impact["direction"],
                )

    def batch_update_agents(self, agents: list[dict]) -> None:
        """Update all agent prices in one transaction after a market tick."""
        with self._session() as session:
            with session.begin_transaction() as tx:
                for agent in agents:
                    tx.run(
                        Q.UPDATE_AGENT_PRICE,
                        agent_id=agent["id"],
                        price=agent["price"],
                        market_cap=agent["market_cap"],
                        volatility=agent["volatility"],
                        inflow_velocity=agent["inflow_velocity"],
                    )

    # ── Contagion endpoint helper ─────────────────────────────────────────────

    def get_contagion_graph(self, shock_id: str | None = None) -> dict:
        """
        Returns graph data suitable for visualization.
        If shock_id given, return contagion path for that shock.
        Otherwise return full capital flow graph.

        TODO (Person A): build nodes/edges structure from query results.
        """
        if shock_id:
            rows = self.run_query("contagion_path", {"shock_id": shock_id})
        else:
            rows = self.run_query("top_inflow", {"limit": 20})

        # TODO: convert rows to nodes/edges format (see docs/GRAPH_SCHEMA.md)
        return {
            "nodes": [],
            "edges": [],
            "query_type": "contagion_path" if shock_id else "top_inflow",
            "raw": rows,
        }
