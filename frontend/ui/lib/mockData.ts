import type {
  Agent, OHLCV, Position, Order, ShockEvent,
  MarketSnapshot, ControlMetrics, AccountInfo, Sector,
} from "./types";

/* ── helpers ──────────────────────────────────────────────────── */

function rand(min: number, max: number) {
  return min + Math.random() * (max - min);
}

function generateSparkline(base: number, len = 20): number[] {
  const pts: number[] = [base];
  for (let i = 1; i < len; i++) {
    pts.push(pts[i - 1] + rand(-base * 0.02, base * 0.02));
  }
  return pts;
}

function generateOHLCV(base: number, count = 60): OHLCV[] {
  const candles: OHLCV[] = [];
  let price = base * rand(0.85, 0.95);
  const now = Date.now();

  for (let i = 0; i < count; i++) {
    const drift = rand(-price * 0.03, price * 0.03);
    const open = price;
    const close = open + drift;
    const high = Math.max(open, close) + rand(0, price * 0.015);
    const low = Math.min(open, close) - rand(0, price * 0.015);
    const volume = Math.round(rand(100, 5000));
    const time = new Date(now - (count - i) * 3600000).toISOString();
    candles.push({ time, open: +open.toFixed(2), high: +high.toFixed(2), low: +low.toFixed(2), close: +close.toFixed(2), volume });
    price = close;
  }
  return candles;
}

/* ── agents ───────────────────────────────────────────────────── */

interface AgentSeed {
  id: string; symbol: string; name: string; sector: Sector;
  price: number; change: number; changePct: number;
}

const seeds: AgentSeed[] = [
  { id: "fraid",  symbol: "FRAID",  name: "Fraud Detection Alpha", sector: "Fraud/AML",  price: 183.86, change: 3.65,   changePct: 1.36 },
  { id: "amlx",   symbol: "AMLX",   name: "AML Compliance Engine", sector: "Fraud/AML",  price: 309.17, change: 40.92,  changePct: 18.11 },
  { id: "compl",  symbol: "COMPL",  name: "Regulatory Compliance", sector: "Compliance",  price: 139.18, change: -9.20,  changePct: -2.05 },
  { id: "geoint", symbol: "GEOINT", name: "Geo Intelligence Hub",  sector: "Geo/OSINT",  price: 293.74, change: 16.63,  changePct: 4.22 },
  { id: "tism",   symbol: "TISM",   name: "Threat Intel Sentinel", sector: "Geo/OSINT",  price: 15.03,  change: -0.53,  changePct: -3.41 },
  { id: "lisc",   symbol: "LISC",   name: "License Validator",     sector: "Compliance",  price: 13.28,  change: 1.07,   changePct: 9.18 },
  { id: "icme",   symbol: "ICME",   name: "Incident Commander",    sector: "Fraud/AML",  price: 491.14, change: 96.02,  changePct: 4.38 },
  { id: "sanct",  symbol: "SANCT",  name: "Sanctions Screener",    sector: "Compliance",  price: 198.21, change: -8.09,  changePct: -5.77 },
];

export const AGENTS: Agent[] = seeds.map((s) => ({
  ...s,
  volume: Math.round(rand(50_000, 500_000)),
  marketCap: +(s.price * rand(80_000, 200_000)).toFixed(0),
  riskScore: +rand(0.1, 0.95).toFixed(2),
  volatility: +rand(5, 35).toFixed(1),
  bid: +(s.price - rand(0.01, 0.15)).toFixed(2),
  ask: +(s.price + rand(0.01, 0.15)).toFixed(2),
  inflowVelocity: +rand(0.5, 8.0).toFixed(1),
  shockSensitivity: +rand(0.2, 0.95).toFixed(2),
  sparkline: generateSparkline(s.price),
}));

/* ── OHLCV per agent ──────────────────────────────────────────── */

export const AGENT_CANDLES: Record<string, OHLCV[]> = {};
for (const a of AGENTS) {
  AGENT_CANDLES[a.id] = generateOHLCV(a.price);
}

/* ── positions ────────────────────────────────────────────────── */

export const POSITIONS: Position[] = [
  { agentId: "fraid",  symbol: "FRAID",  name: "Fraud Detection Alpha", qty: 1.031, avgCost: 135.60, mktValue: 189.54, dayReturn: 2.01,    dayReturnPct: 1.07, totalReturn: 49.94,    totalReturnPct: 35.81 },
  { agentId: "amlx",   symbol: "AMLX",   name: "AML Compliance Engine", qty: 11.43, avgCost: 475.85, mktValue: 5439.91, dayReturn: -237.65, dayReturnPct: -4.18, totalReturn: -1.94,   totalReturnPct: -0.04 },
  { agentId: "geoint", symbol: "GEOINT", name: "Geo Intelligence Hub",  qty: 2,     avgCost: 5219.96, mktValue: 10439.91, dayReturn: 532.68, dayReturnPct: 5.38, totalReturn: 0,       totalReturnPct: 0 },
  { agentId: "icme",   symbol: "ICME",   name: "Incident Commander",    qty: 2.04,  avgCost: 21.57,   mktValue: 39.91,    dayReturn: 12.01,  dayReturnPct: 43.07, totalReturn: -3.27,  totalReturnPct: -7.57 },
  { agentId: "lisc",   symbol: "LISC",   name: "License Validator",     qty: 2.04,  avgCost: 21.57,   mktValue: 39.91,    dayReturn: 12.01,  dayReturnPct: 43.07, totalReturn: -3.27,  totalReturnPct: -7.57 },
  { agentId: "compl",  symbol: "COMPL",  name: "Regulatory Compliance", qty: 1,     avgCost: 39.91,   mktValue: 39.91,    dayReturn: -20.01, dayReturnPct: -1.32, totalReturn: 0,      totalReturnPct: 0 },
  { agentId: "sanct",  symbol: "SANCT",  name: "Sanctions Screener",    qty: 3.56,  avgCost: 248.69,  mktValue: 885.35,   dayReturn: -62.01, dayReturnPct: -6.54, totalReturn: 0.96,   totalReturnPct: 0.11 },
  { agentId: "tism",   symbol: "TISM",   name: "Threat Intel Sentinel", qty: 44.58, avgCost: 211.53,  mktValue: 9439.91,  dayReturn: -188.05, dayReturnPct: -1.95, totalReturn: 14.38, totalReturnPct: 0.15 },
];

/* ── orders ───────────────────────────────────────────────────── */

const now = new Date();
function ago(minBack: number) {
  return new Date(now.getTime() - minBack * 60000).toISOString();
}

export const ORDERS: Order[] = [
  { id: "o1",  agentId: "lisc",   symbol: "LISC",   side: "sell", type: "market",      status: "working",   qty: 5,    price: 13.28, filledQty: 0,    filledPrice: null,   timestamp: ago(2) },
  { id: "o2",  agentId: "fraid",  symbol: "FRAID",  side: "buy",  type: "market",      status: "filled",    qty: 1,    price: 183.86, filledQty: 1,   filledPrice: 183.86, timestamp: ago(5) },
  { id: "o3",  agentId: "amlx",   symbol: "AMLX",   side: "sell", type: "limit",       status: "filled",    qty: 2,    price: 315.00, filledQty: 2,   filledPrice: 315.02, timestamp: ago(12) },
  { id: "o4",  agentId: "compl",  symbol: "COMPL",  side: "sell", type: "stop_market", status: "cancelled", qty: 1,    price: 130.00, filledQty: 0,   filledPrice: null,   timestamp: ago(15) },
  { id: "o5",  agentId: "icme",   symbol: "ICME",   side: "buy",  type: "market",      status: "filled",    qty: 2,    price: 491.14, filledQty: 2,   filledPrice: 490.88, timestamp: ago(22) },
  { id: "o6",  agentId: "fraid",  symbol: "FRAID",  side: "buy",  type: "limit",       status: "filled",    qty: 0.5,  price: 180.00, filledQty: 0.5, filledPrice: 179.95, timestamp: ago(30) },
  { id: "o7",  agentId: "geoint", symbol: "GEOINT", side: "sell", type: "stop_market", status: "cancelled", qty: 1,    price: 280.00, filledQty: 0,   filledPrice: null,   timestamp: ago(45) },
  { id: "o8",  agentId: "sanct",  symbol: "SANCT",  side: "buy",  type: "market",      status: "filled",    qty: 3,    price: 198.21, filledQty: 3,   filledPrice: 198.19, timestamp: ago(55) },
  { id: "o9",  agentId: "tism",   symbol: "TISM",   side: "buy",  type: "market",      status: "filled",    qty: 20,   price: 15.03,  filledQty: 20,  filledPrice: 15.01,  timestamp: ago(60) },
  { id: "o10", agentId: "fraid",  symbol: "FRAID",  side: "sell", type: "limit",       status: "working",   qty: 1,    price: 190.00, filledQty: 0,   filledPrice: null,   timestamp: ago(1) },
];

/* ── shock log ────────────────────────────────────────────────── */

export const SHOCK_LOG: ShockEvent[] = [
  { id: "s1", type: "REGULATION",  severity: 0.7, timestamp: ago(120), affectedAgents: ["compl", "lisc", "sanct"], description: "New SEC directive on AI agent disclosures" },
  { id: "s2", type: "CYBER",       severity: 0.85, timestamp: ago(90),  affectedAgents: ["fraid", "amlx", "icme"], description: "Coordinated DDoS on fraud-detection networks" },
  { id: "s3", type: "FX_SHOCK",    severity: 0.5,  timestamp: ago(60),  affectedAgents: ["geoint", "tism"],        description: "JPY flash crash spills into OSINT pricing" },
];

/* ── market snapshot ──────────────────────────────────────────── */

export const MARKET_SNAPSHOT: MarketSnapshot = {
  totalMarketCap: AGENTS.reduce((s, a) => s + a.marketCap, 0),
  totalVolume: AGENTS.reduce((s, a) => s + a.volume, 0),
  cascadeProbability: 0.14,
  activeShocks: 1,
  agentCount: AGENTS.length,
  lastUpdate: new Date().toISOString(),
};

/* ── control metrics ──────────────────────────────────────────── */

export const CONTROL_METRICS: ControlMetrics = {
  cascadeProbability: 0.14,
  lastRunId: "run-a7f3c1e2",
  bedrockTokens: 12847,
  bedrockLatencyMs: 1243,
  engineTickMs: 48,
  neo4jNodes: 1247,
  neo4jEdges: 3891,
  uptime: "4d 7h 22m",
};

/* ── account ──────────────────────────────────────────────────── */

export const ACCOUNT: AccountInfo = {
  name: "Individual",
  balance: 26523.12,
  dayPL: 201.82,
  dayPLPct: 0.14,
  buyingPower: 13320.36,
  optionsBuyingPower: 9283.10,
  balanceHistory: [
    25800, 25950, 26100, 25900, 25700, 25850, 26000, 26200,
    26050, 26150, 26300, 26100, 26250, 26400, 26350, 26523,
  ],
};
