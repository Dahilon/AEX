"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { createMarketSocket } from "../lib/api";
import type { Agent, ShockEvent, WsMessage, EventLogEntry } from "../types/market";

interface MarketStreamState {
  agents: Record<string, Partial<Agent>>;  // live price overrides keyed by agent_id
  totalMarketCap: number;
  cascadeProbability: number;
  activeShocks: number;
  latestShock: ShockEvent | null;
  eventLog: EventLogEntry[];
  connected: boolean;
}

interface UseMarketStreamReturn extends MarketStreamState {
  clearEvents: () => void;
}

const MAX_LOG_ENTRIES = 50;

export function useMarketStream(): UseMarketStreamReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [state, setState] = useState<MarketStreamState>({
    agents: {},
    totalMarketCap: 0,
    cascadeProbability: 0,
    activeShocks: 0,
    latestShock: null,
    eventLog: [],
    connected: false,
  });

  const addLogEntry = useCallback((message: string, level: EventLogEntry["level"], tag?: string) => {
    const entry: EventLogEntry = {
      id: `${Date.now()}-${Math.random()}`,
      timestamp: Date.now() / 1000,
      message,
      level,
      tag,
    };
    setState(prev => ({
      ...prev,
      eventLog: [entry, ...prev.eventLog].slice(0, MAX_LOG_ENTRIES),
    }));
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = createMarketSocket();
      wsRef.current = ws;

      ws.onopen = () => {
        setState(prev => ({ ...prev, connected: true }));
        addLogEntry("Connected to market stream", "success", "SYSTEM");
      };

      ws.onclose = () => {
        setState(prev => ({ ...prev, connected: false }));
        addLogEntry("Disconnected from market stream — reconnecting in 3s...", "warn", "SYSTEM");
        // Auto-reconnect
        reconnectTimer.current = setTimeout(connect, 3000);
      };

      ws.onerror = (err) => {
        addLogEntry("WebSocket error", "error", "SYSTEM");
      };

      ws.onmessage = (event) => {
        try {
          const msg: WsMessage = JSON.parse(event.data as string);
          handleMessage(msg);
        } catch (e) {
          console.warn("Failed to parse WS message", e);
        }
      };
    } catch (e) {
      addLogEntry("Failed to connect to market stream", "error", "SYSTEM");
    }
  }, [addLogEntry]);

  const handleMessage = useCallback((msg: WsMessage) => {
    if (msg.type === "tick") {
      const agentUpdates: Record<string, Partial<Agent>> = {};
      for (const a of msg.agents) {
        agentUpdates[a.id] = {
          price: a.price,
          price_change_pct: a.price_change_pct,
          inflow_velocity: a.inflow_velocity,
          inflow_direction: a.inflow_direction,
        };
      }
      setState(prev => ({
        ...prev,
        agents: { ...prev.agents, ...agentUpdates },
        totalMarketCap: msg.total_market_cap,
        cascadeProbability: msg.cascade_probability,
        activeShocks: msg.active_shocks,
      }));
    } else if (msg.type === "shock") {
      setState(prev => ({ ...prev, latestShock: msg.shock }));
      addLogEntry(
        `${msg.shock.type} shock (severity: ${msg.shock.severity.toFixed(2)}) — ${msg.shock.description}`,
        "warn",
        "SHOCK",
      );
    } else if (msg.type === "event") {
      addLogEntry(msg.message, msg.level, "EVENT");
    }
  }, [addLogEntry]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const clearEvents = useCallback(() => {
    setState(prev => ({ ...prev, eventLog: [] }));
  }, []);

  return { ...state, clearEvents };
}
