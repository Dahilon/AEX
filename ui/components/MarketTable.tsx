"use client";

import { useState } from "react";
import type { Agent } from "../types/market";

interface MarketTableProps {
  agents: Agent[];
  liveUpdates: Record<string, Partial<Agent>>;
  onAgentClick?: (agent: Agent) => void;
}

const SECTOR_COLORS: Record<string, string> = {
  FRAUD_AML:  "bg-red-900/40 text-red-300 border border-red-700",
  COMPLIANCE: "bg-blue-900/40 text-blue-300 border border-blue-700",
  GEO_OSINT:  "bg-green-900/40 text-green-300 border border-green-700",
};

const SECTOR_LABELS: Record<string, string> = {
  FRAUD_AML:  "Fraud/AML",
  COMPLIANCE: "Compliance",
  GEO_OSINT:  "Geo OSINT",
};

type SortField = "name" | "price" | "price_change_pct" | "market_cap" | "volatility" | "risk_score";

function riskBar(score: number) {
  const color = score < 0.35 ? "bg-green-500" : score < 0.55 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-1">
      <div className="w-16 bg-gray-700 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${score * 100}%` }} />
      </div>
      <span className="text-xs text-gray-400">{(score * 100).toFixed(0)}%</span>
    </div>
  );
}

function inflowArrow(direction: string) {
  if (direction === "up")   return <span className="text-green-400 font-bold">↑</span>;
  if (direction === "down") return <span className="text-red-400 font-bold">↓</span>;
  return <span className="text-gray-500">—</span>;
}

export function MarketTable({ agents, liveUpdates, onAgentClick }: MarketTableProps) {
  const [sortField, setSortField] = useState<SortField>("market_cap");
  const [sortDir, setSortDir] = useState<1 | -1>(-1);

  function handleSort(field: SortField) {
    if (sortField === field) {
      setSortDir(d => (d === 1 ? -1 : 1));
    } else {
      setSortField(field);
      setSortDir(-1);
    }
  }

  // Merge live updates onto base agent data
  const mergedAgents: Agent[] = agents.map(a => ({
    ...a,
    ...(liveUpdates[a.id] ?? {}),
  }));

  const sorted = [...mergedAgents].sort((a, b) => {
    const av = a[sortField] as number | string;
    const bv = b[sortField] as number | string;
    if (typeof av === "number" && typeof bv === "number") return (av - bv) * sortDir;
    return String(av).localeCompare(String(bv)) * sortDir;
  });

  function SortHeader({ field, label }: { field: SortField; label: string }) {
    const active = sortField === field;
    return (
      <th
        className={`px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider cursor-pointer select-none hover:text-white transition-colors ${active ? "text-blue-400" : "text-gray-400"}`}
        onClick={() => handleSort(field)}
      >
        {label} {active ? (sortDir === 1 ? "↑" : "↓") : ""}
      </th>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-gray-700">
            <SortHeader field="name" label="Agent" />
            <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-gray-400">Sector</th>
            <SortHeader field="price" label="Price" />
            <SortHeader field="price_change_pct" label="24h %" />
            <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-gray-400">Inflow</th>
            <SortHeader field="volatility" label="Vol" />
            <SortHeader field="market_cap" label="Mkt Cap" />
            <SortHeader field="risk_score" label="Risk" />
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {sorted.map(agent => {
            const pct = agent.price_change_pct;
            const pctColor = pct > 0 ? "text-green-400" : pct < 0 ? "text-red-400" : "text-gray-400";
            const pctStr = `${pct > 0 ? "+" : ""}${pct.toFixed(2)}%`;

            return (
              <tr
                key={agent.id}
                className="hover:bg-gray-800/60 transition-colors cursor-pointer"
                onClick={() => onAgentClick?.(agent)}
              >
                <td className="px-3 py-2.5 font-medium text-white">{agent.name}</td>
                <td className="px-3 py-2.5">
                  <span className={`px-1.5 py-0.5 rounded text-xs ${SECTOR_COLORS[agent.sector]}`}>
                    {SECTOR_LABELS[agent.sector]}
                  </span>
                </td>
                <td className="px-3 py-2.5 font-mono text-white font-semibold">
                  ${agent.price.toFixed(2)}
                </td>
                <td className={`px-3 py-2.5 font-mono font-semibold ${pctColor}`}>{pctStr}</td>
                <td className="px-3 py-2.5">
                  <span className="flex items-center gap-1">
                    {inflowArrow(agent.inflow_direction)}
                    <span className="text-gray-400 font-mono text-xs">
                      {Math.abs(agent.inflow_velocity).toFixed(3)}
                    </span>
                  </span>
                </td>
                <td className="px-3 py-2.5 font-mono text-gray-300">{agent.volatility.toFixed(3)}</td>
                <td className="px-3 py-2.5 font-mono text-gray-200">
                  ${(agent.market_cap / 1000).toFixed(1)}K
                </td>
                <td className="px-3 py-2.5">{riskBar(agent.risk_score)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
