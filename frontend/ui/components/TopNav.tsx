"use client";

import { Activity, Plus, Settings, Wifi, WifiOff, User } from "lucide-react";
import { useAEX, type BottomTab } from "@/lib/store";

const TABS = [
  { id: "trading" as const, label: "Trading" },
  { id: "monitoring" as const, label: "Monitoring" },
];

export function TopNav() {
  const { bottomTab, setBottomTab, snapshot } = useAEX();

  return (
    <header className="h-11 flex items-center justify-between px-4 border-b border-border-subtle bg-surface-1/80 backdrop-blur-[16px] shrink-0 z-50">
      {/* Left: logo + market status */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <Activity className="w-4 h-4 text-accent" />
          <span className="text-sm font-semibold tracking-tight text-white">AEX</span>
        </div>
        <div className="h-4 w-px bg-border-subtle" />
        <span className="pill bg-gain/15 text-gain flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-gain animate-pulse" />
          Market Open
        </span>
      </div>

      {/* Center: tabs */}
      <nav className="flex items-center gap-1">
        {TABS.map((tab) => {
          const active = (tab.id === "trading" && bottomTab === "orders") ||
                         (tab.id === "trading" && bottomTab === "shocks") ||
                         (tab.id === "monitoring" && bottomTab === "monitoring");
          return (
            <button
              key={tab.id}
              onClick={() => {
                const map: Record<string, BottomTab> = { trading: "orders", monitoring: "monitoring" };
                setBottomTab(map[tab.id] ?? "orders");
              }}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                active ? "bg-surface-3 text-white" : "text-gray-500 hover:text-gray-300"
              }`}
            >
              {tab.label}
            </button>
          );
        })}
        <button className="p-1 rounded-md text-gray-600 hover:text-gray-400 transition-colors">
          <Plus className="w-3.5 h-3.5" />
        </button>
      </nav>

      {/* Right: settings + avatar */}
      <div className="flex items-center gap-2">
        <span className="text-[10px] text-gray-500 font-mono tabular-nums">
          {snapshot.agentCount} agents
        </span>
        <button className="p-1.5 rounded-md text-gray-500 hover:text-gray-300 hover:bg-surface-3/60 transition-colors">
          <Settings className="w-3.5 h-3.5" />
        </button>
        <div className="w-6 h-6 rounded-full bg-surface-4 flex items-center justify-center">
          <User className="w-3.5 h-3.5 text-gray-400" />
        </div>
      </div>
    </header>
  );
}
