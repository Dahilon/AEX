// ============================================================
// AEX — Shared TypeScript types
// Keep in sync with services/market_engine/models.py
// ============================================================

export type Sector = "FRAUD_AML" | "COMPLIANCE" | "GEO_OSINT";

export type ShockType =
  | "REGULATION"
  | "CYBER"
  | "FX_SHOCK"
  | "EARTHQUAKE"
  | "SANCTIONS";

export type InflowDirection = "up" | "down" | "flat";

// Agent as returned by GET /market/agents
export interface Agent {
  id: string;
  name: string;
  sector: Sector;
  price: number;
  price_change_pct: number;
  market_cap: number;
  usage_score: number;
  performance_score: number;
  reliability_score: number;
  risk_score: number;
  inflow_velocity: number;
  inflow_direction: InflowDirection;
  volatility: number;
  total_backing: number;
}

export interface SectorSummary {
  id: Sector;
  avg_price_change_pct: number;
  total_market_cap: number;
  agent_count: number;
}

export interface ShockEvent {
  id: string;
  type: ShockType;
  severity: number;          // 0.0–1.0
  description: string;
  timestamp: number;         // unix timestamp
  ticks_remaining: number;
  source: string;
}

// Full snapshot from GET /market/snapshot
export interface MarketSnapshot {
  tick_number: number;
  total_market_cap: number;
  cascade_probability: number;
  active_shocks: ShockEvent[];
  agents: Agent[];
  sectors: SectorSummary[];
}

// WebSocket tick update from WS /market/stream
export type WsMessageType = "tick" | "shock" | "event";

export interface WsTickMessage {
  type: "tick";
  tick_number: number;
  agents: Pick<Agent, "id" | "price" | "price_change_pct" | "inflow_velocity" | "inflow_direction">[];
  total_market_cap: number;
  active_shocks: number;
  cascade_probability: number;
}

export interface WsShockMessage {
  type: "shock";
  shock: ShockEvent;
}

export interface WsEventMessage {
  type: "event";
  message: string;
  timestamp: number;
  level: "info" | "warn" | "error";
}

export type WsMessage = WsTickMessage | WsShockMessage | WsEventMessage;

// POST /shock/inject request body
export interface InjectShockRequest {
  shock_type: ShockType;
  severity?: number;         // optional override (default auto-computed)
  description?: string;      // optional override
}

// POST /analysis/run response
export interface AnalysisResult {
  text: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
  cached: boolean;
}

// POST /analysis/risk response
export interface RiskResult {
  text: string;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  model: string;
  cached: boolean;
}

// POST /tests/run response
export interface TestResult {
  test_name: string;
  status: "PASS" | "FAIL" | "ERROR";
  duration_ms: number;
  details: Record<string, unknown>;
  error?: string;
}

export interface TestResults {
  results: TestResult[];
  summary: string;           // e.g. "2/2 PASSED"
}

// GET /graph/contagion response
export interface GraphNode {
  id: string;
  label: string;             // "User" | "Agent" | "CapitalPool" | "Sector" | "ShockEvent"
  properties: Record<string, unknown>;
}

export interface GraphEdge {
  from: string;
  to: string;
  type: string;              // "ALLOCATES" | "BACKS" | "IN_SECTOR" | "IMPACTS"
  properties: Record<string, unknown>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  query_type: string;
}

// Log entry for EventLog component
export interface EventLogEntry {
  id: string;
  timestamp: number;
  message: string;
  level: "info" | "warn" | "error" | "success";
  tag?: string;              // e.g. "SHOCK", "TICK", "ANALYSIS", "TEST"
}
