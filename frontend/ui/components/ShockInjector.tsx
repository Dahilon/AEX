"use client";

import { useState } from "react";
import { useAEX } from "@/lib/store";
import { injectShock } from "@/lib/api";
import type { ShockType } from "@/lib/types";
import { Zap, AlertTriangle } from "lucide-react";

const SHOCK_TYPES: { value: ShockType; label: string; icon: string }[] = [
  { value: "REGULATION",  label: "Regulation",  icon: "📋" },
  { value: "CYBER",       label: "Cyber Attack", icon: "🔒" },
  { value: "FX_SHOCK",    label: "FX Spike",     icon: "💱" },
  { value: "EARTHQUAKE",  label: "Earthquake",   icon: "🌍" },
  { value: "SANCTIONS",   label: "Sanctions",    icon: "🚫" },
];

export function ShockInjector() {
  const { shockLog, addShock } = useAEX();
  const [shockType, setShockType] = useState<ShockType>("REGULATION");
  const [severity, setSeverity] = useState(0.5);
  const [injecting, setInjecting] = useState(false);

  async function handleInject() {
    setInjecting(true);
    try {
      const shock = await injectShock(shockType, severity);
      addShock(shock);
    } finally {
      setInjecting(false);
    }
  }

  return (
    <div className="flex gap-4 h-full p-3">
      {/* Controls */}
      <div className="w-64 shrink-0 space-y-3">
        <div className="flex items-center gap-1.5">
          <Zap className="w-3.5 h-3.5 text-yellow-400" />
          <span className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Inject shock</span>
        </div>

        {/* Type selector */}
        <div className="space-y-1">
          <label className="text-[10px] text-gray-500">Type</label>
          <select
            value={shockType}
            onChange={(e) => setShockType(e.target.value as ShockType)}
            className="w-full bg-surface-0/50 border border-border-subtle rounded-md px-2 py-1.5 text-xs text-white outline-none focus:border-accent/50"
          >
            {SHOCK_TYPES.map((s) => (
              <option key={s.value} value={s.value}>{s.icon} {s.label}</option>
            ))}
          </select>
        </div>

        {/* Severity slider */}
        <div className="space-y-1">
          <div className="flex justify-between">
            <label className="text-[10px] text-gray-500">Severity</label>
            <span className="text-[10px] font-mono text-gray-400">{severity.toFixed(2)}</span>
          </div>
          <input
            type="range"
            min="0.1"
            max="1.0"
            step="0.05"
            value={severity}
            onChange={(e) => setSeverity(parseFloat(e.target.value))}
            className="w-full h-1 accent-yellow-400 rounded-full appearance-none bg-surface-4 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-yellow-400"
          />
        </div>

        <button
          onClick={handleInject}
          disabled={injecting}
          className="w-full py-1.5 rounded-lg text-xs font-semibold bg-yellow-500/15 text-yellow-400 border border-yellow-500/30 hover:bg-yellow-500/25 transition-all disabled:opacity-40 active:scale-[0.98]"
        >
          {injecting ? "Injecting..." : "Inject Shock"}
        </button>
      </div>

      {/* Event log */}
      <div className="flex-1 min-w-0">
        <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1.5 flex items-center gap-1">
          <AlertTriangle className="w-3 h-3" /> Event log
        </div>
        <div className="space-y-1 overflow-y-auto max-h-[120px]">
          {shockLog.map((s) => (
            <div key={s.id} className="flex items-start gap-2 px-2 py-1 bg-surface-0/40 rounded text-[11px]">
              <span className="text-yellow-400 shrink-0">
                {SHOCK_TYPES.find((st) => st.value === s.type)?.icon ?? "⚡"}
              </span>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-300">{s.type}</span>
                  <span className="text-gray-600 font-mono text-[9px]">sev {s.severity.toFixed(2)}</span>
                </div>
                <p className="text-gray-500 text-[10px] truncate">{s.description}</p>
              </div>
              <span className="ml-auto text-[9px] text-gray-600 font-mono shrink-0 tabular-nums">
                {new Date(s.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </span>
            </div>
          ))}
          {shockLog.length === 0 && (
            <p className="text-[11px] text-gray-600 italic">No shocks injected yet</p>
          )}
        </div>
      </div>
    </div>
  );
}
