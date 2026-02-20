/**
 * AEX API client
 * All backend calls go through this file.
 * Set USE_MOCK=true to work without a backend.
 */

import type {
  Agent, MarketSnapshot, ShockEvent, InjectShockRequest,
  AnalysisResult, RiskResult, TestResults, GraphData, ShockType,
} from "../types/market";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ── Toggle mock mode for frontend-only development ────────────────────────────
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }
  return res.json() as Promise<T>;
}

// ── Market endpoints ──────────────────────────────────────────────────────────

export async function fetchAgents(): Promise<Agent[]> {
  if (USE_MOCK) return MOCK_AGENTS;
  return apiFetch<Agent[]>("/market/agents");
}

export async function fetchAgent(agentId: string): Promise<Agent & { price_history: number[] }> {
  return apiFetch(`/market/agents/${agentId}`);
}

export async function fetchSnapshot(): Promise<MarketSnapshot> {
  if (USE_MOCK) return MOCK_SNAPSHOT;
  return apiFetch<MarketSnapshot>("/market/snapshot");
}

export async function buyAgent(agentId: string, amount: number): Promise<void> {
  await apiFetch(`/market/agents/${agentId}/buy?amount=${amount}`, { method: "POST" });
}

export async function sellAgent(agentId: string, amount: number): Promise<void> {
  await apiFetch(`/market/agents/${agentId}/sell?amount=${amount}`, { method: "POST" });
}

// ── Shock endpoints ───────────────────────────────────────────────────────────

export async function injectShock(
  shockType: ShockType,
  severity?: number,
  description?: string,
): Promise<ShockEvent> {
  if (USE_MOCK) return MOCK_SHOCK;
  return apiFetch<ShockEvent>("/shock/inject", {
    method: "POST",
    body: JSON.stringify({ shock_type: shockType, severity, description } satisfies InjectShockRequest),
  });
}

// ── Analysis endpoints ────────────────────────────────────────────────────────

export async function runAnalysis(question?: string): Promise<AnalysisResult> {
  if (USE_MOCK) return MOCK_ANALYSIS;
  return apiFetch<AnalysisResult>("/analysis/run", {
    method: "POST",
    body: JSON.stringify({ question: question ?? "Analyze the current market state." }),
  });
}

export async function runRiskAnalysis(): Promise<RiskResult> {
  if (USE_MOCK) return MOCK_RISK;
  return apiFetch<RiskResult>("/analysis/risk", { method: "POST" });
}

// ── Graph endpoint ────────────────────────────────────────────────────────────

export async function fetchContagionGraph(shockId?: string): Promise<GraphData> {
  const qs = shockId ? `?shock_id=${shockId}` : "";
  return apiFetch<GraphData>(`/graph/contagion${qs}`);
}

// ── Tests endpoint ────────────────────────────────────────────────────────────

export async function runTests(testName: string = "all"): Promise<TestResults> {
  return apiFetch<TestResults>("/tests/run", {
    method: "POST",
    body: JSON.stringify({ test_name: testName }),
  });
}

// ── Audio summary endpoint ────────────────────────────────────────────────────

export async function fetchAudioSummary(text: string): Promise<{ audio_url: string }> {
  return apiFetch<{ audio_url: string }>("/audio/summary", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

// ── WebSocket factory ─────────────────────────────────────────────────────────

export function createMarketSocket(): WebSocket {
  const wsUrl = API_URL.replace(/^http/, "ws") + "/market/stream";
  return new WebSocket(wsUrl);
}

// ── Mock data (for USE_MOCK=true) ─────────────────────────────────────────────

const MOCK_AGENTS: Agent[] = [
  { id: "fraudguard_v3", name: "FraudGuard-v3", sector: "FRAUD_AML", price: 142.50, price_change_pct: -3.2, market_cap: 712500, usage_score: 0.85, performance_score: 0.78, reliability_score: 0.92, risk_score: 0.35, inflow_velocity: -0.08, inflow_direction: "down", volatility: 0.045, total_backing: 5000 },
  { id: "complibot_eu", name: "CompliBot-EU", sector: "COMPLIANCE", price: 224.10, price_change_pct: 6.7, market_cap: 1456650, usage_score: 0.90, performance_score: 0.85, reliability_score: 0.90, risk_score: 0.20, inflow_velocity: 0.22, inflow_direction: "up", volatility: 0.062, total_backing: 6500 },
  { id: "amlscan_pro", name: "AMLScan-Pro", sector: "FRAUD_AML", price: 95.10, price_change_pct: -2.1, market_cap: 361380, usage_score: 0.72, performance_score: 0.81, reliability_score: 0.88, risk_score: 0.42, inflow_velocity: -0.03, inflow_direction: "down", volatility: 0.033, total_backing: 3800 },
  { id: "regwatch_us", name: "RegWatch-US", sector: "COMPLIANCE", price: 171.00, price_change_pct: 3.4, market_cap: 718200, usage_score: 0.78, performance_score: 0.82, reliability_score: 0.87, risk_score: 0.25, inflow_velocity: 0.10, inflow_direction: "up", volatility: 0.040, total_backing: 4200 },
  { id: "geointel_live", name: "GeoIntel-Live", sector: "GEO_OSINT", price: 55.20, price_change_pct: -1.1, market_cap: 99360, usage_score: 0.70, performance_score: 0.68, reliability_score: 0.80, risk_score: 0.55, inflow_velocity: -0.05, inflow_direction: "down", volatility: 0.055, total_backing: 1800 },
];

const MOCK_SNAPSHOT: MarketSnapshot = {
  tick_number: 145,
  total_market_cap: 3348090,
  cascade_probability: 0.28,
  active_shocks: [],
  agents: MOCK_AGENTS,
  sectors: [
    { id: "FRAUD_AML", avg_price_change_pct: -2.65, total_market_cap: 1073880, agent_count: 2 },
    { id: "COMPLIANCE", avg_price_change_pct: 5.05, total_market_cap: 2174850, agent_count: 2 },
    { id: "GEO_OSINT", avg_price_change_pct: -1.10, total_market_cap: 99360, agent_count: 1 },
  ],
};

const MOCK_SHOCK: ShockEvent = {
  id: "mock_01",
  type: "REGULATION",
  severity: 0.7,
  description: "Regulatory crackdown on AI systems announced",
  timestamp: Date.now() / 1000,
  ticks_remaining: 4,
  source: "manual",
};

const MOCK_ANALYSIS: AnalysisResult = {
  text: "**Market Update**: The REGULATION shock (severity 0.7) triggered a sector rotation. Compliance agents surged +6.7% led by CompliBot-EU, while Fraud/AML agents dropped -2.8% on average.\n\n**Key Findings:**\n- CompliBot-EU saw inflow_velocity jump to 0.22, driving its price to $224.10\n- FraudGuard-v3 lost backing as capital rotated into safer Compliance plays\n- Cascade probability remains low at 0.28\n\n**Recommended Action:** Overweight COMPLIANCE, reduce GEO_OSINT exposure until shock decays.\n\n*This is a simulated market analysis.*",
  model: "anthropic.claude-3-5-sonnet",
  input_tokens: 1240,
  output_tokens: 187,
  latency_ms: 2340,
  cached: false,
};

const MOCK_RISK: RiskResult = {
  text: "RISK LEVEL: LOW\n\n[CONCENTRATION] CompliBot-EU has 38% of CapitalPool backing — approaching threshold.\n[BUBBLE] CompliBot-EU price +6.7% while performance delta is only +0.02 — watch for correction.\n\nCascade Assessment: 28% probability. If CompliBot-EU corrects sharply, RegWatch-US most at risk due to shared pool overlap.\n\n*This is a simulated risk assessment.*",
  risk_level: "LOW",
  model: "anthropic.claude-3-5-sonnet",
  cached: false,
};
