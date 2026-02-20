"use client";

import { useState } from "react";
import type { ShockType, ShockEvent } from "../types/market";
import { injectShock } from "../lib/api";

interface ShockInjectorProps {
  onShockInjected: (shock: ShockEvent) => void;
}

const SHOCKS: { label: string; value: ShockType; description: string; emoji: string }[] = [
  { label: "Regulation Crackdown", value: "REGULATION", emoji: "⚖️",  description: "EU AI Act enforcement — Compliance up, Fraud/AML down" },
  { label: "Cyber Attack",         value: "CYBER",      emoji: "💻",  description: "Major breach detected — Geo/OSINT and Fraud agents surge" },
  { label: "FX Spike",             value: "FX_SHOCK",   emoji: "💱",  description: "USD/EUR moves 1.2% — broad market volatility" },
  { label: "Earthquake",           value: "EARTHQUAKE", emoji: "🌍",  description: "M6.2 near Singapore — GeoIntel demand spikes" },
  { label: "Sanctions Package",    value: "SANCTIONS",  emoji: "🚫",  description: "New OFAC sanctions — Compliance and Fraud/AML benefit" },
];

export function ShockInjector({ onShockInjected }: ShockInjectorProps) {
  const [loading, setLoading] = useState<ShockType | null>(null);
  const [lastInjected, setLastInjected] = useState<ShockEvent | null>(null);

  async function handleInject(shockType: ShockType) {
    if (loading) return;
    setLoading(shockType);
    try {
      const shock = await injectShock(shockType);
      setLastInjected(shock);
      onShockInjected(shock);
    } catch (e) {
      console.error("Shock injection failed", e);
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">
        ⚡ Inject Market Shock
      </h3>
      <div className="grid grid-cols-1 gap-2">
        {SHOCKS.map(shock => (
          <button
            key={shock.value}
            onClick={() => handleInject(shock.value)}
            disabled={loading !== null}
            className="w-full text-left px-3 py-2.5 bg-gray-700 hover:bg-gray-600 border border-gray-600 hover:border-orange-500 rounded-lg transition-all group disabled:opacity-50"
          >
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-sm text-white">
                {shock.emoji} {shock.label}
              </span>
              {loading === shock.value && (
                <span className="text-xs text-orange-400 animate-pulse">Injecting...</span>
              )}
            </div>
            <p className="text-xs text-gray-400 mt-0.5 group-hover:text-gray-300 transition-colors">
              {shock.description}
            </p>
          </button>
        ))}
      </div>

      {lastInjected && (
        <div className="mt-3 p-2 bg-orange-900/30 border border-orange-700 rounded-lg">
          <p className="text-xs text-orange-300">
            ✓ Injected: <strong>{lastInjected.type}</strong> (severity: {(lastInjected.severity * 100).toFixed(0)}%)
          </p>
          <p className="text-xs text-gray-400 mt-0.5">{lastInjected.description}</p>
        </div>
      )}
    </div>
  );
}
