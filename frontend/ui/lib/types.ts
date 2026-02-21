export type Sector = "Fraud/AML" | "Compliance" | "Geo/OSINT";
export type ShockType = "REGULATION" | "CYBER" | "FX_SHOCK" | "EARTHQUAKE" | "SANCTIONS";
export type OrderSide = "buy" | "sell";
export type OrderType = "market" | "limit" | "stop_market";
export type OrderStatus = "working" | "filled" | "cancelled";

export interface Agent {
  id: string;
  symbol: string;
  name: string;
  sector: Sector;
  price: number;
  change: number;
  changePct: number;
  volume: number;
  marketCap: number;
  riskScore: number;
  volatility: number;
  bid: number;
  ask: number;
  inflowVelocity: number;
  shockSensitivity: number;
  sparkline: number[];
}

export interface OHLCV {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface Position {
  agentId: string;
  symbol: string;
  name: string;
  qty: number;
  avgCost: number;
  mktValue: number;
  dayReturn: number;
  dayReturnPct: number;
  totalReturn: number;
  totalReturnPct: number;
}

export interface Order {
  id: string;
  agentId: string;
  symbol: string;
  side: OrderSide;
  type: OrderType;
  status: OrderStatus;
  qty: number;
  price: number;
  filledQty: number;
  filledPrice: number | null;
  timestamp: string;
}

export interface ShockEvent {
  id: string;
  type: ShockType;
  severity: number;
  timestamp: string;
  affectedAgents: string[];
  description: string;
}

export interface MarketSnapshot {
  totalMarketCap: number;
  totalVolume: number;
  cascadeProbability: number;
  activeShocks: number;
  agentCount: number;
  lastUpdate: string;
}

export interface ControlMetrics {
  cascadeProbability: number;
  lastRunId: string;
  bedrockTokens: number;
  bedrockLatencyMs: number;
  engineTickMs: number;
  neo4jNodes: number;
  neo4jEdges: number;
  uptime: string;
}

export interface AnalysisResult {
  text: string;
  runId: string;
  tokens: number;
  latencyMs: number;
  timestamp: string;
}

export interface AccountInfo {
  name: string;
  balance: number;
  dayPL: number;
  dayPLPct: number;
  buyingPower: number;
  optionsBuyingPower: number;
  balanceHistory: number[];
}
