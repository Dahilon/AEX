"use client";

import type { EventLogEntry } from "../types/market";

interface EventLogProps {
  entries: EventLogEntry[];
  onClear: () => void;
}

const LEVEL_COLORS: Record<string, string> = {
  info:    "text-gray-400",
  warn:    "text-orange-400",
  error:   "text-red-400",
  success: "text-green-400",
};

const TAG_COLORS: Record<string, string> = {
  SHOCK:    "bg-orange-900/50 text-orange-300 border-orange-700",
  TICK:     "bg-gray-700 text-gray-400 border-gray-600",
  ANALYSIS: "bg-blue-900/50 text-blue-300 border-blue-700",
  TEST:     "bg-purple-900/50 text-purple-300 border-purple-700",
  SYSTEM:   "bg-gray-800 text-gray-500 border-gray-700",
  EVENT:    "bg-gray-700 text-gray-300 border-gray-600",
};

function formatTime(ts: number): string {
  return new Date(ts * 1000).toLocaleTimeString("en-US", {
    hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
}

export function EventLog({ entries, onClear }: EventLogProps) {
  return (
    <div className="bg-gray-900/70 border border-gray-700 rounded-xl">
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-700">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Event Log</h3>
        <button
          onClick={onClear}
          className="text-xs text-gray-600 hover:text-gray-400 transition-colors"
        >
          Clear
        </button>
      </div>
      <div className="overflow-y-auto max-h-40 divide-y divide-gray-800">
        {entries.length === 0 && (
          <div className="px-4 py-3 text-xs text-gray-600 italic">Waiting for events...</div>
        )}
        {entries.map(entry => (
          <div key={entry.id} className="flex items-start gap-2 px-4 py-2 hover:bg-gray-800/40 transition-colors">
            <span className="text-gray-600 font-mono text-xs shrink-0 pt-0.5">
              {formatTime(entry.timestamp)}
            </span>
            {entry.tag && (
              <span className={`px-1.5 py-0.5 rounded text-xs border shrink-0 font-mono ${TAG_COLORS[entry.tag] ?? "bg-gray-700 text-gray-400 border-gray-600"}`}>
                {entry.tag}
              </span>
            )}
            <span className={`text-xs leading-tight ${LEVEL_COLORS[entry.level]}`}>
              {entry.message}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
