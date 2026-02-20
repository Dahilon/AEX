"""
Tool implementations for Bedrock agents.

These are called when Bedrock returns a tool_use block.
market_snapshot() → current market state
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.services.market_engine.engine import MarketEngine

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
]


class ToolExecutor:
    """
    Executes tool calls from Bedrock agents.
    Injected with engine at startup.
    """

    def __init__(self, engine: "MarketEngine"):
        self.engine = engine

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
