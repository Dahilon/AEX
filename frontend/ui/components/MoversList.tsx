"use client";

import { useState } from "react";
import { useAEX } from "@/lib/store";
import { Sparkline } from "./Sparkline";
import type { Sector } from "@/lib/types";

type Filter = "All" | Sector;
const FILTERS: Filter[] = ["All", "Fraud/AML", "Compliance", "Geo/OSINT"];

export function MoversList() {
  const { agents, selectedAgentId, selectAgent } = useAEX();
  const [filter, setFilter] = useState<Filter>("All");

  const filtered = filter === "All" ? agents : agents.filter((a) => a.sector === filter);
  const sorted = [...filtered].sort((a, b) => Math.abs(b.changePct) - Math.abs(a.changePct));

  return (
    <div className="flex flex-col min-h-0">
      {/* Header */}
      <div className="px-3 py-2 border-b border-border-subtle flex items-center justify-between">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Market movers</span>
      </div>

      {/* Sector filter */}
      <div className="px-2 py-1.5 flex gap-1 overflow-x-auto border-b border-border-subtle">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-2 py-0.5 rounded text-[10px] font-medium whitespace-nowrap transition-colors ${
              filter === f
                ? "bg-surface-4 text-white"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Column header */}
      <div className="grid grid-cols-[20px_1fr_60px_56px_44px] gap-1 px-3 py-1 text-[9px] text-gray-600 uppercase tracking-wider font-medium">
        <span>#</span>
        <span>Symbol</span>
        <span className="text-right">Last</span>
        <span className="text-right">Net chg</span>
        <span className="text-right">%</span>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {sorted.map((agent, i) => {
          const selected = agent.id === selectedAgentId;
          const up = agent.changePct >= 0;
          return (
            <button
              key={agent.id}
              onClick={() => selectAgent(agent.id)}
              className={`w-full grid grid-cols-[20px_1fr_60px_56px_44px] gap-1 items-center px-3 py-1.5 text-left transition-colors ${
                selected
                  ? "bg-accent/10 border-l-2 border-accent"
                  : "hover:bg-surface-3/40 border-l-2 border-transparent"
              }`}
            >
              <span className="text-[10px] text-gray-600 tabular-nums">{i + 1}</span>
              <div className="flex items-center gap-1.5 min-w-0">
                <span className="text-xs font-semibold text-white truncate">{agent.symbol}</span>
                <Sparkline data={agent.sparkline} width={32} height={12} />
              </div>
              <span className="text-xs font-mono tabular-nums text-gray-200 text-right">
                ${agent.price.toFixed(2)}
              </span>
              <span className={`text-[11px] font-mono tabular-nums text-right ${up ? "text-gain" : "text-loss"}`}>
                {up ? "+" : ""}${agent.change.toFixed(2)}
              </span>
              <span className={`text-[11px] font-mono tabular-nums text-right ${up ? "text-gain" : "text-loss"}`}>
                {up ? "+" : ""}{agent.changePct.toFixed(1)}%
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
