"use client";

import type { ShockType } from "../types/market";

const SHOCK_OPTIONS: { label: string; value: ShockType; emoji: string }[] = [
  { label: "Regulation Crackdown", value: "REGULATION", emoji: "⚖️" },
  { label: "Cyber Attack",         value: "CYBER",      emoji: "💻" },
  { label: "FX Spike",             value: "FX_SHOCK",   emoji: "💱" },
  { label: "Earthquake",           value: "EARTHQUAKE", emoji: "🌍" },
  { label: "Sanctions",            value: "SANCTIONS",  emoji: "🚫" },
];

interface HeaderProps {
  totalMarketCap: number;
  cascadeProbability: number;
  activeShocks: number;
  connected: boolean;
  onInjectShock: (type: ShockType) => void;
  onRunAnalysis: () => void;
  onRunRisk: () => void;
  onRunTests: () => void;
  analysisLoading: boolean;
  testsLoading: boolean;
}

export function Header({
  totalMarketCap,
  cascadeProbability,
  activeShocks,
  connected,
  onInjectShock,
  onRunAnalysis,
  onRunRisk,
  onRunTests,
  analysisLoading,
  testsLoading,
}: HeaderProps) {
  const cascadeColor =
    cascadeProbability > 0.6
      ? "text-red-400"
      : cascadeProbability > 0.35
      ? "text-yellow-400"
      : "text-green-400";

  return (
    <header className="border-b border-gray-700 bg-gray-900/80 backdrop-blur px-6 py-3 flex items-center justify-between gap-4 flex-wrap">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="text-2xl font-bold text-white tracking-tight">
          AEX <span className="text-blue-400">↗</span>
        </div>
        <div className="text-xs text-gray-500 hidden sm:block">Agent Exchange</div>
        <div className={`w-2 h-2 rounded-full ml-2 ${connected ? "bg-green-400 animate-pulse" : "bg-red-500"}`} />
      </div>

      {/* Market stats */}
      <div className="flex items-center gap-6 text-sm">
        <div>
          <span className="text-gray-500 text-xs">Total Mkt Cap </span>
          <span className="text-white font-mono font-semibold">
            ${(totalMarketCap / 1_000_000).toFixed(2)}M
          </span>
        </div>
        <div>
          <span className="text-gray-500 text-xs">Cascade Risk </span>
          <span className={`font-mono font-semibold ${cascadeColor}`}>
            {(cascadeProbability * 100).toFixed(1)}%
          </span>
        </div>
        {activeShocks > 0 && (
          <div className="flex items-center gap-1">
            <span className="inline-block w-2 h-2 bg-orange-400 rounded-full animate-ping" />
            <span className="text-orange-400 text-xs font-semibold">{activeShocks} active shock{activeShocks > 1 ? "s" : ""}</span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 flex-wrap">
        {/* Shock dropdown */}
        <div className="relative group">
          <button className="px-3 py-1.5 bg-orange-600 hover:bg-orange-500 text-white text-sm rounded-md font-medium transition-colors flex items-center gap-1">
            ⚡ Inject Shock ▾
          </button>
          <div className="absolute right-0 mt-1 w-52 bg-gray-800 border border-gray-600 rounded-lg shadow-xl z-50 hidden group-hover:block">
            {SHOCK_OPTIONS.map(opt => (
              <button
                key={opt.value}
                className="w-full text-left px-4 py-2.5 text-sm text-gray-200 hover:bg-gray-700 hover:text-white transition-colors flex items-center gap-2"
                onClick={() => onInjectShock(opt.value)}
              >
                <span>{opt.emoji}</span> {opt.label}
              </button>
            ))}
          </div>
        </div>

        <button
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-md font-medium transition-colors disabled:opacity-50"
          onClick={onRunAnalysis}
          disabled={analysisLoading}
        >
          {analysisLoading ? "Analyzing..." : "Run Analysis"}
        </button>

        <button
          className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white text-sm rounded-md font-medium transition-colors"
          onClick={onRunRisk}
        >
          Risk Check
        </button>

        <button
          className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-md font-medium transition-colors disabled:opacity-50"
          onClick={onRunTests}
          disabled={testsLoading}
        >
          {testsLoading ? "Running..." : "Run Tests"}
        </button>
      </div>
    </header>
  );
}
