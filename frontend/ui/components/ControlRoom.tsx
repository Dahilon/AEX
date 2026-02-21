"use client";

import { useAEX } from "@/lib/store";
import { Activity, Database, ExternalLink, Gauge, Clock, Cpu, Waypoints } from "lucide-react";

export function ControlRoom() {
  const { controlMetrics: m, snapshot } = useAEX();

  const ddUrl = process.env.NEXT_PUBLIC_DATADOG_DASHBOARD_URL || "#";
  const neo4jUrl = process.env.NEXT_PUBLIC_NEO4J_GRAPH_URL || "#";

  const metrics = [
    { icon: Gauge,     label: "Cascade prob.",   value: `${(m.cascadeProbability * 100).toFixed(0)}%`, color: m.cascadeProbability > 0.2 ? "text-yellow-400" : "text-gain" },
    { icon: Activity,  label: "Last run_id",     value: m.lastRunId,           color: "text-accent" },
    { icon: Cpu,       label: "Bedrock tokens",  value: m.bedrockTokens.toLocaleString(), color: "text-gray-300" },
    { icon: Clock,     label: "Bedrock latency", value: `${m.bedrockLatencyMs}ms`,        color: m.bedrockLatencyMs > 1500 ? "text-yellow-400" : "text-gray-300" },
    { icon: Clock,     label: "Engine tick",     value: `${m.engineTickMs}ms`,             color: m.engineTickMs > 100 ? "text-loss" : "text-gain" },
    { icon: Waypoints, label: "Neo4j graph",     value: `${m.neo4jNodes} nodes · ${m.neo4jEdges} edges`, color: "text-gray-300" },
    { icon: Database,  label: "Active shocks",   value: snapshot.activeShocks.toString(),  color: snapshot.activeShocks > 0 ? "text-orange-400" : "text-gray-300" },
    { icon: Activity,  label: "Uptime",          value: m.uptime,              color: "text-gray-300" },
  ];

  return (
    <div className="flex gap-4 h-full p-3">
      {/* Metrics grid */}
      <div className="flex-1 grid grid-cols-4 gap-2">
        {metrics.map((met) => (
          <div key={met.label} className="bg-surface-0/40 rounded-lg px-2.5 py-2">
            <div className="flex items-center gap-1 mb-1">
              <met.icon className="w-3 h-3 text-gray-500" />
              <span className="text-[9px] text-gray-500 uppercase tracking-wider">{met.label}</span>
            </div>
            <span className={`text-xs font-mono tabular-nums ${met.color}`}>{met.value}</span>
          </div>
        ))}
      </div>

      {/* External links */}
      <div className="w-44 shrink-0 flex flex-col gap-2">
        <a
          href={ddUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400 text-xs font-medium hover:bg-purple-500/20 transition-colors"
        >
          <ExternalLink className="w-3.5 h-3.5" />
          Open Datadog
        </a>
        <a
          href={neo4jUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-medium hover:bg-cyan-500/20 transition-colors"
        >
          <Waypoints className="w-3.5 h-3.5" />
          Open Neo4j Graph
        </a>
        <div className="mt-auto text-[9px] text-gray-600 font-mono">
          Last update: {new Date(snapshot.lastUpdate).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}
