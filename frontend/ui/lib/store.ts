import { create } from "zustand";
import type {
  Agent, OHLCV, Position, Order, ShockEvent,
  MarketSnapshot, ControlMetrics, AnalysisResult, AccountInfo,
} from "./types";
import {
  AGENTS, POSITIONS, ORDERS, SHOCK_LOG,
  MARKET_SNAPSHOT, CONTROL_METRICS, ACCOUNT, AGENT_CANDLES,
} from "./mockData";

export type BottomTab = "orders" | "shocks" | "monitoring";

interface AEXState {
  agents: Agent[];
  selectedAgentId: string;
  candles: Record<string, OHLCV[]>;
  positions: Position[];
  orders: Order[];
  shockLog: ShockEvent[];
  snapshot: MarketSnapshot;
  controlMetrics: ControlMetrics;
  account: AccountInfo;
  bottomTab: BottomTab;
  analysisOpen: boolean;
  analysisResult: AnalysisResult | null;
  analysisLoading: boolean;

  selectAgent: (id: string) => void;
  addOrder: (order: Order) => void;
  addShock: (shock: ShockEvent) => void;
  setBottomTab: (tab: BottomTab) => void;
  openAnalysis: (result: AnalysisResult) => void;
  closeAnalysis: () => void;
  setAnalysisLoading: (v: boolean) => void;
}

export const useAEX = create<AEXState>((set) => ({
  agents: AGENTS,
  selectedAgentId: AGENTS[0].id,
  candles: AGENT_CANDLES,
  positions: POSITIONS,
  orders: ORDERS,
  shockLog: SHOCK_LOG,
  snapshot: MARKET_SNAPSHOT,
  controlMetrics: CONTROL_METRICS,
  account: ACCOUNT,
  bottomTab: "orders",
  analysisOpen: false,
  analysisResult: null,
  analysisLoading: false,

  selectAgent: (id) => set({ selectedAgentId: id }),
  addOrder: (order) => set((s) => ({ orders: [order, ...s.orders] })),
  addShock: (shock) => set((s) => ({ shockLog: [shock, ...s.shockLog] })),
  setBottomTab: (tab) => set({ bottomTab: tab }),
  openAnalysis: (result) => set({ analysisOpen: true, analysisResult: result, analysisLoading: false }),
  closeAnalysis: () => set({ analysisOpen: false }),
  setAnalysisLoading: (v) => set({ analysisLoading: v }),
}));
