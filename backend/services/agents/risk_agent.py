"""
Bedrock Risk Agent — same pattern as market_analyst but with surveillance focus.
See docs/AGENTS_SPEC.md for full spec.
"""

import json
import logging
import os
import time
import boto3
# from ddtrace.llmobs import LLMObs

from .tools import TOOL_DEFINITIONS, ToolExecutor

logger = logging.getLogger(__name__)

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")

SYSTEM_PROMPT = """You are the AEX Risk Agent — a market surveillance AI for the AEX agent market simulation.

CRITICAL RULES:
- This is a SIMULATION. All data is simulated.
- NEVER reference real financial markets or instruments.
- Be conservative: flag risks early, explain clearly.

YOUR JOB:
1. Detect concentration risk (single pool dominates an agent's backing).
2. Identify potential manipulation patterns (wash trading, pump-and-dump).
3. Calculate cascade probability (if one agent crashes, how many follow?).
4. Flag bubble conditions (price disconnected from fundamentals).

FORMAT:
- Lead with RISK LEVEL: LOW / MEDIUM / HIGH / CRITICAL.
- List each risk finding as: [RISK TYPE] Description + Evidence.
- End with "Cascade Assessment" — probability and which agents are most at risk.
- Always cite specific metrics (HHI values, inflow numbers, price/fundamental gaps).
- Keep response under 350 words."""

RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class RiskAgent:
    def __init__(self, tool_executor: ToolExecutor):
        self.executor = tool_executor
        self._bedrock = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        self._cache: dict | None = None

    def analyze(self) -> dict:
        """
        Run the Risk Agent.
        Returns: { text, risk_level, model, cached }
        """
        start = time.time()

        try:
            result = self._run_with_tools()
        except Exception as e:
            logger.error(f"Risk Agent Bedrock call failed: {e}", exc_info=True)
            if self._cache:
                self._cache["cached"] = True
                return self._cache
            return {"text": "[Risk analysis unavailable]", "risk_level": "MEDIUM", "model": MODEL_ID, "cached": True}

        result["latency_ms"] = round((time.time() - start) * 1000)
        result["cached"] = False
        self._cache = result
        return result

    def _run_with_tools(self) -> dict:
        prompt = (
            "Perform a full risk assessment of the current AEX market. "
            "Check concentration risk, look for manipulation signals, and compute cascade probability."
        )
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        final_text = ""

        with LLMObs.llm(model_name=MODEL_ID, model_provider="bedrock", name="risk_agent") as llm_span:
            for _ in range(3):
                response = self._bedrock.converse(
                    modelId=MODEL_ID,
                    system=[{"text": SYSTEM_PROMPT}],
                    messages=messages,
                    toolConfig={"tools": TOOL_DEFINITIONS},
                    inferenceConfig={"maxTokens": 500, "temperature": 0.2},
                )

                stop_reason = response["stopReason"]
                output_content = response["output"]["message"]["content"]
                messages.append({"role": "assistant", "content": output_content})

                if stop_reason == "end_turn":
                    for block in output_content:
                        if "text" in block:
                            final_text = block["text"]
                    break

                elif stop_reason == "tool_use":
                    tool_results = []
                    for block in output_content:
                        if "toolUse" in block:
                            tu = block["toolUse"]
                            result_str = self.executor.execute(tu["name"], tu["input"])
                            tool_results.append({
                                "toolResult": {
                                    "toolUseId": tu["toolUseId"],
                                    "content": [{"text": result_str}],
                                }
                            })
                    messages.append({"role": "user", "content": tool_results})

            LLMObs.annotate(
                span=llm_span,
                input_data=[{"role": "user", "content": prompt}],
                output_data=[{"role": "assistant", "content": final_text}],
            )

        risk_level = self._extract_risk_level(final_text)
        return {"text": final_text or "[No risk assessment generated]", "risk_level": risk_level, "model": MODEL_ID}

    def _extract_risk_level(self, text: str) -> str:
        text_upper = text.upper()
        for level in reversed(RISK_LEVELS):  # check CRITICAL first
            if level in text_upper:
                return level
        return "MEDIUM"
