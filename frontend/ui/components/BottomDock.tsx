"use client";

import { useAEX, type BottomTab } from "@/lib/store";
import { ShockInjector } from "./ShockInjector";
import { ControlRoom } from "./ControlRoom";
import { List, Zap, Monitor, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

const TABS: { id: BottomTab; label: string; icon: typeof List }[] = [
  { id: "orders",     label: "Orders",       icon: List },
  { id: "shocks",     label: "Shocks",       icon: Zap },
  { id: "monitoring", label: "Control Room",  icon: Monitor },
];

export function BottomDock() {
  const { bottomTab, setBottomTab, orders } = useAEX();
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="border-t border-border-subtle bg-surface-1/60 backdrop-blur-[16px] flex flex-col shrink-0">
      {/* Tab bar */}
      <div className="flex items-center h-8 px-2 gap-1 border-b border-border-subtle">
        {TABS.map((tab) => {
          const active = bottomTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => { setBottomTab(tab.id); if (!expanded) setExpanded(true); }}
              className={`flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${
                active ? "bg-surface-3 text-white" : "text-gray-500 hover:text-gray-300"
              }`}
            >
              <tab.icon className="w-3 h-3" />
              {tab.label}
            </button>
          );
        })}
        <button
          onClick={() => setExpanded(!expanded)}
          className="ml-auto p-1 rounded text-gray-500 hover:text-gray-300 transition-colors"
        >
          {expanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Content */}
      {expanded && (
        <div className="h-[160px] overflow-hidden animate-slide-up">
          {bottomTab === "orders" && (
            <div className="h-full overflow-auto">
              <table className="w-full text-[11px]">
                <thead>
                  <tr className="text-gray-500 text-[9px] uppercase tracking-wider border-b border-border-subtle">
                    <th className="px-3 py-1.5 text-left font-medium">Symbol</th>
                    <th className="px-3 py-1.5 text-left font-medium">Side</th>
                    <th className="px-3 py-1.5 text-left font-medium">Type</th>
                    <th className="px-3 py-1.5 text-right font-medium">Qty</th>
                    <th className="px-3 py-1.5 text-right font-medium">Price</th>
                    <th className="px-3 py-1.5 text-left font-medium">Status</th>
                    <th className="px-3 py-1.5 text-right font-medium">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((o) => (
                    <tr key={o.id} className="border-b border-border-subtle/30 hover:bg-surface-3/20 transition-colors">
                      <td className="px-3 py-1.5 font-semibold text-white">{o.symbol}</td>
                      <td className={`px-3 py-1.5 font-medium ${o.side === "buy" ? "text-gain" : "text-loss"}`}>
                        {o.side.charAt(0).toUpperCase() + o.side.slice(1)}
                      </td>
                      <td className="px-3 py-1.5 text-gray-400 capitalize">
                        {o.type === "stop_market" ? "Stop" : o.type}
                      </td>
                      <td className="px-3 py-1.5 text-right font-mono tabular-nums text-gray-300">{o.qty}</td>
                      <td className="px-3 py-1.5 text-right font-mono tabular-nums text-gray-300">
                        ${(o.filledPrice ?? o.price).toFixed(2)}
                      </td>
                      <td className="px-3 py-1.5">
                        <span className={`pill ${
                          o.status === "filled" ? "bg-gain/15 text-gain" :
                          o.status === "cancelled" ? "bg-loss/15 text-loss" :
                          "bg-blue-500/15 text-blue-400"
                        }`}>
                          {o.status.charAt(0).toUpperCase() + o.status.slice(1)}
                        </span>
                      </td>
                      <td className="px-3 py-1.5 text-right font-mono tabular-nums text-gray-500">
                        {new Date(o.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {bottomTab === "shocks" && <ShockInjector />}
          {bottomTab === "monitoring" && <ControlRoom />}
        </div>
      )}
    </div>
  );
}
