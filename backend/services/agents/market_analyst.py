"""
Bedrock Market Analyst Agent.

Uses the Converse API with tool-use to:
1. Call market_snapshot() to get current market state
2. Call graph_query() to get graph data
3. Return a structured analysis

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
FALLBACK_MODEL_ID = "amazon.nova-pro-v1:0"
MAX_TOOL_ROUNDS = 3
TIMEOUT_S = 15.0

SYSTEM_PROMPT = """You are the AEX Market Analyst — an AI agent that analyzes a simulated market of AI agents.

CRITICAL RULES:
- This is a SIMULATION. All prices, agents, and capital flows are simulated.
- NEVER reference real stocks, real companies, or real financial instruments.
- NEVER give real financial advice. Always clarify this is a simulation.
- Base ALL analysis on data from your tools. Do not hallucinate metrics.

YOUR JOB:
1. Explain price movements by correlating with shock events and metric changes.
2. Identify top movers and the reasons behind their moves.
3. Predict short-term direction (next 1-3 ticks) based on current trends.
4. Suggest allocation adjustments (which agents to overweight/underweight).

FORMAT:
- Lead with a 1-sentence summary.
- Use bullet points for key findings.
- End with a "Recommended Action" section.
- Always cite which metric or shock drove your conclusion.
- Keep response under 400 words."""


class MarketAnalystAgent:
    def __init__(self, tool_executor: ToolExecutor):
        self.executor = tool_executor
        self._bedrock = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        self._cache: dict | None = None

    def analyze(self, user_question: str = "Analyze the current market state and explain what's happening.") -> dict:
        """
        Run the Market Analyst agent.
        Returns: { text, model, input_tokens, output_tokens, latency_ms, cached }
        """
        start = time.time()

        try:
            result = self._run_with_tools(user_question)
        except Exception as e:
            logger.error(f"Bedrock call failed: {e}", exc_info=True)
            if self._cache:
                self._cache["cached"] = True
                return self._cache
            return {
                "text": f"[Analysis unavailable: {str(e)}]",
                "model": MODEL_ID,
                "input_tokens": 0,
                "output_tokens": 0,
                "latency_ms": 0,
                "cached": True,
            }

        result["latency_ms"] = round((time.time() - start) * 1000)
        result["cached"] = False
        self._cache = result
        return result

    def _run_with_tools(self, user_question: str) -> dict:
        messages = [{"role": "user", "content": [{"text": user_question}]}]
        total_input_tokens = 0
        total_output_tokens = 0
        final_text = ""

        with LLMObs.llm(
            model_name=MODEL_ID,
            model_provider="bedrock",
            name="market_analyst",
        ) as llm_span:
            for round_num in range(MAX_TOOL_ROUNDS):
                response = self._bedrock.converse(
                    modelId=MODEL_ID,
                    system=[{"text": SYSTEM_PROMPT}],
                    messages=messages,
                    toolConfig={"tools": TOOL_DEFINITIONS},
                    inferenceConfig={"maxTokens": 600, "temperature": 0.3},
                )

                usage = response.get("usage", {})
                total_input_tokens  += usage.get("inputTokens", 0)
                total_output_tokens += usage.get("outputTokens", 0)

                stop_reason = response["stopReason"]
                output_content = response["output"]["message"]["content"]

                messages.append({"role": "assistant", "content": output_content})

                if stop_reason == "end_turn":
                    # Extract text from response
                    for block in output_content:
                        if "text" in block:
                            final_text = block["text"]
                    break

                elif stop_reason == "tool_use":
                    # Execute all tool calls and add results to messages
                    tool_results = []
                    for block in output_content:
                        if "toolUse" in block:
                            tool_use = block["toolUse"]
                            tool_result = self.executor.execute(
                                tool_use["name"],
                                tool_use["input"],
                            )
                            tool_results.append({
                                "toolResult": {
                                    "toolUseId": tool_use["toolUseId"],
                                    "content": [{"text": tool_result}],
                                }
                            })

                    messages.append({"role": "user", "content": tool_results})

                else:
                    logger.warning(f"Unexpected stop_reason: {stop_reason}")
                    break

            # Annotate LLM Obs span
            LLMObs.annotate(
                span=llm_span,
                input_data=[{"role": "user", "content": user_question}],
                output_data=[{"role": "assistant", "content": final_text}],
                metrics={
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens,
                },
            )

        return {
            "text": final_text or "[No analysis generated]",
            "model": MODEL_ID,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
        }
