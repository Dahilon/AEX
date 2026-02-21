import type { Agent, MarketSnapshot, AnalysisResult, ShockEvent, ShockType, Order } from "./types";
import { AGENTS, MARKET_SNAPSHOT, SHOCK_LOG, AGENT_CANDLES } from "./mockData";

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

export async function fetchMarketAgents(): Promise<Agent[]> {
  await delay(300);
  return AGENTS;
}

export async function fetchMarketSnapshot(): Promise<MarketSnapshot> {
  await delay(200);
  return MARKET_SNAPSHOT;
}

export async function fetchAgentCandles(agentId: string) {
  await delay(250);
  return AGENT_CANDLES[agentId] ?? [];
}

export async function runAnalysis(question?: string): Promise<AnalysisResult> {
  await delay(1500);
  return {
    text: question
      ? `Analysis for "${question}":\n\nThe AEX market shows moderate volatility across Fraud/AML agents with AMLX leading gains at +18.11%. Compliance sector is under pressure following the recent REGULATION shock (severity 0.70). Geo/OSINT agents remain stable with GEOINT showing healthy inflow velocity.\n\nCascade probability sits at 14% — below the 25% threshold but worth monitoring given the active CYBER shock affecting fraud-detection networks.\n\nRecommendation: Consider reducing exposure to SANCT (-5.77%) and rotating into LISC (+9.18%) which shows strong momentum with low shock sensitivity.`
      : `Market Overview:\n\nTotal market cap: $${(MARKET_SNAPSHOT.totalMarketCap / 1e6).toFixed(1)}M across ${MARKET_SNAPSHOT.agentCount} agents. Volume is elevated at ${MARKET_SNAPSHOT.totalVolume.toLocaleString()} units.\n\nKey observations:\n• AMLX leads all movers (+18.11%) on strong inflow velocity\n• Compliance sector under pressure from REGULATION shock\n• Cascade probability at 14% — stable but elevated\n• 1 active shock affecting 3 agents\n\nNo immediate systemic risk detected.`,
    runId: "run-" + Math.random().toString(36).slice(2, 10),
    tokens: Math.round(800 + Math.random() * 600),
    latencyMs: Math.round(1000 + Math.random() * 800),
    timestamp: new Date().toISOString(),
  };
}

export async function injectShock(type: ShockType, severity: number): Promise<ShockEvent> {
  await delay(800);
  const descriptions: Record<ShockType, string> = {
    REGULATION: "Emergency regulatory directive issued",
    CYBER: "Coordinated cyber attack detected",
    FX_SHOCK: "Foreign exchange flash crash event",
    EARTHQUAKE: "Major seismic event affecting infrastructure",
    SANCTIONS: "New international sanctions package announced",
  };
  return {
    id: "s-" + Math.random().toString(36).slice(2, 10),
    type,
    severity,
    timestamp: new Date().toISOString(),
    affectedAgents: AGENTS.slice(0, Math.ceil(Math.random() * 4)).map((a) => a.id),
    description: descriptions[type],
  };
}

export async function runTests(suite: string): Promise<{ passed: number; failed: number; total: number }> {
  await delay(2000);
  const total = 24;
  const failed = Math.floor(Math.random() * 3);
  return { passed: total - failed, failed, total };
}

export async function placeOrder(order: Omit<Order, "id" | "timestamp" | "filledQty" | "filledPrice" | "status">): Promise<Order> {
  await delay(400);
  return {
    ...order,
    id: "o-" + Math.random().toString(36).slice(2, 10),
    status: order.type === "market" ? "filled" : "working",
    filledQty: order.type === "market" ? order.qty : 0,
    filledPrice: order.type === "market" ? order.price * (1 + (Math.random() - 0.5) * 0.002) : null,
    timestamp: new Date().toISOString(),
  };
}
