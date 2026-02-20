"""
Tool implementations for Bedrock agents.

These are called when Bedrock returns a tool_use block.
market_snapshot() → current market state
graph_query()     → Neo4j graph query result
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.market_engine.engine import MarketEngine
    from services.graph.service import GraphService

logger = logging.getLogger(__name__)

# Tool definitions in Bedrock format (passed as toolConfig)
TOOL_DEFINITIONS = [
    {
        "toolSpec": {
            "name": "market_snapshot",
            "description": (
                "Returns the current state of all agents in the AEX simulated market. "
                "Includes prices, fundamentals, sector averages, and recent shocks. "
                "Use this to understand current market conditions."
            ),
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "include_history": {
                            "type": "boolean",
                            "description": "If true, include last 20 price ticks per agent",
                        },
                        "sector_filter": {
                            "type": "string",
                            "description": "Optional: filter to a specific sector",
                            "enum": ["FRAUD_AML", "COMPLIANCE", "GEO_OSINT"],
                        },
                    },
                    "required": [],
                }
            },
        }
    },
    {
        "toolSpec": {
            "name": "graph_query",
            "description": (
                "Query the capital flow graph to understand how capital moves through "
                "the market. Returns data about inflows, concentration risk, and contagion paths."
            ),
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "query_type": {
                            "type": "string",
                            "description": "Type of query to run",
                            "enum": [
                                "top_inflow",
                                "concentration_risk",
                                "contagion_path",
                                "cross_sector_exposure",
                                "most_impacted_users",
                            ],
                        },
                        "params": {
                            "type": "object",
                            "description": "Optional query parameters (e.g., shock_id, limit)",
                        },
                    },
                    "required": ["query_type"],
                }
            },
        }
    },
]


class ToolExecutor:
    """
    Executes tool calls from Bedrock agents.
    Injected with engine and graph_service at startup.
    """

    def __init__(self, engine: "MarketEngine", graph_service: "GraphService"):
        self.engine = engine
        self.graph_service = graph_service

    def execute(self, tool_name: str, tool_input: dict) -> str:
        """
        Execute a tool call and return JSON string result.
        Called when Bedrock returns stopReason='tool_use'.
        """
        import json

        logger.info(f"Tool call: {tool_name} with input: {tool_input}")

        try:
            if tool_name == "market_snapshot":
                result = self._market_snapshot(tool_input)
            elif tool_name == "graph_query":
                result = self._graph_query(tool_input)
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Tool execution error: {e}", exc_info=True)
            result = {"error": str(e)}

        return json.dumps(result)

    def _market_snapshot(self, tool_input: dict) -> dict:
        snapshot = self.engine.get_snapshot()
        sector_filter = tool_input.get("sector_filter")

        if sector_filter:
            snapshot["agents"] = [
                a for a in snapshot["agents"] if a["sector"] == sector_filter
            ]

        if not tool_input.get("include_history", False):
            # Strip price_history to keep response concise
            for agent in snapshot["agents"]:
                agent.pop("price_history", None)

        return snapshot

    def _graph_query(self, tool_input: dict) -> dict:
        query_type = tool_input["query_type"]
        params = tool_input.get("params", {})
        rows = self.graph_service.run_query(query_type, params)
        return {
            "query_type": query_type,
            "results": rows,
        }
