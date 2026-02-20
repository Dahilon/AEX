"use client";

import { useState, useEffect, useCallback } from "react";
import { useCopilotReadable, useCopilotAction } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

import { Header }         from "../components/Header";
import { MarketTable }    from "../components/MarketTable";
import { ShockInjector }  from "../components/ShockInjector";
import { AnalysisPanel }  from "../components/AnalysisPanel";
import { EventLog }       from "../components/EventLog";
import { TestResults }    from "../components/TestResults";
import { useMarketStream } from "../hooks/useMarketStream";

import {
  fetchAgents, fetchSnapshot,
  runAnalysis, runRiskAnalysis, runTests, injectShock,
} from "../lib/api";
import type {
  Agent, MarketSnapshot, AnalysisResult, RiskResult,
  TestResults as TestResultsType, ShockEvent, ShockType,
} from "../types/market";

export default function Home() {
  // ── Base data (from REST on load) ────────────────────────────────────────
  const [agents, setAgents] = useState<Agent[]>([]);
  const [snapshot, setSnapshot] = useState<MarketSnapshot | null>(null);

  // ── Live updates (from WebSocket) ────────────────────────────────────────
  const {
    agents: liveUpdates,
    totalMarketCap,
    cascadeProbability,
    activeShocks,
    latestShock,
    eventLog,
    connected,
    clearEvents,
  } = useMarketStream();

  // ── Analysis state ───────────────────────────────────────────────────────
  const [analysis, setAnalysis]       = useState<AnalysisResult | null>(null);
  const [riskResult, setRiskResult]   = useState<RiskResult | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  // ── Test state ───────────────────────────────────────────────────────────
  const [testResults, setTestResults] = useState<TestResultsType | null>(null);
  const [testsLoading, setTestsLoading] = useState(false);

  // ── Initial data load ─────────────────────────────────────────────────────
  useEffect(() => {
    fetchAgents().then(setAgents).catch(console.error);
    fetchSnapshot().then(setSnapshot).catch(console.error);
  }, []);

  // Refresh agents periodically (backup if WS disconnects)
  useEffect(() => {
    const interval = setInterval(() => {
      fetchAgents().then(setAgents).catch(() => {});
    }, 10_000);
    return () => clearInterval(interval);
  }, []);

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleRunAnalysis = useCallback(async (question?: string) => {
    setAnalysisLoading(true);
    try {
      const result = await runAnalysis(question);
      setAnalysis(result);
    } catch (e) {
      console.error("Analysis failed", e);
    } finally {
      setAnalysisLoading(false);
    }
  }, []);

  const handleRunRisk = useCallback(async () => {
    const result = await runRiskAnalysis().catch(() => null);
    if (result) setRiskResult(result);
  }, []);

  const handleRunTests = useCallback(async () => {
    setTestsLoading(true);
    try {
      const results = await runTests("all");
      setTestResults(results);
    } finally {
      setTestsLoading(false);
    }
  }, []);

  const handleInjectShock = useCallback(async (type: ShockType) => {
    await injectShock(type).catch(console.error);
  }, []);

  const handleShockFromInjector = useCallback((shock: ShockEvent) => {
    // WS will broadcast the shock back — eventLog updated via stream hook
  }, []);

  // ── CopilotKit integration ─────────────────────────────────────────────────

  useCopilotReadable({
    description: "Current AEX market state with all agents and active shocks",
    value: snapshot ?? { message: "Market data loading..." },
  });

  useCopilotAction({
    name: "analyzeMarket",
    description: "Run the Bedrock Market Analyst to explain current market conditions",
    parameters: [
      { name: "question", type: "string", description: "Specific question about the market" },
    ],
    handler: async ({ question }) => {
      await handleRunAnalysis(question as string | undefined);
      return analysis?.text ?? "Analysis complete. Check the Analysis panel.";
    },
  });

  useCopilotAction({
    name: "injectMarketShock",
    description: "Inject a market shock event to simulate a real-world disruption",
    parameters: [
      {
        name: "shock_type",
        type: "string",
        description: "Type of shock: REGULATION, CYBER, FX_SHOCK, EARTHQUAKE, or SANCTIONS",
      },
    ],
    handler: async ({ shock_type }) => {
      await handleInjectShock(shock_type as ShockType);
      return `Injected ${shock_type} shock into the market.`;
    },
  });

  useCopilotAction({
    name: "runRiskCheck",
    description: "Run the Risk Agent to detect concentration, manipulation, and cascade risks",
    parameters: [],
    handler: async () => {
      await handleRunRisk();
      return riskResult?.text ?? "Risk check complete. Check the Analysis panel.";
    },
  });

  // ── Merged market cap (prefer WS data, fallback to REST) ──────────────────
  const displayMarketCap = totalMarketCap || snapshot?.total_market_cap || 0;
  const displayCascade   = cascadeProbability || snapshot?.cascade_probability || 0;

  return (
    <CopilotSidebar
      defaultOpen={false}
      labels={{
        title: "AEX Market Assistant",
        initial: "Ask about any agent, sector, or market condition. I can inject shocks and run analysis for you.",
      }}
    >
      <div className="flex flex-col h-screen overflow-hidden">
        {/* Header */}
        <Header
          totalMarketCap={displayMarketCap}
          cascadeProbability={displayCascade}
          activeShocks={activeShocks}
          connected={connected}
          onInjectShock={handleInjectShock}
          onRunAnalysis={() => handleRunAnalysis()}
          onRunRisk={handleRunRisk}
          onRunTests={handleRunTests}
          analysisLoading={analysisLoading}
          testsLoading={testsLoading}
        />

        {/* Main content */}
        <div className="flex-1 overflow-hidden flex flex-col">
          <div className="flex-1 overflow-auto p-4 grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Left: Market table (takes 2/3) */}
            <div className="lg:col-span-2 flex flex-col gap-4">
              <div className="bg-gray-800/50 border border-gray-700 rounded-xl overflow-hidden">
                <div className="px-4 py-2.5 border-b border-gray-700 flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Agent Market</h2>
                  <span className="text-xs text-gray-500">
                    {agents.length} agents · click row to expand
                  </span>
                </div>
                <MarketTable
                  agents={agents}
                  liveUpdates={liveUpdates}
                />
              </div>

              {/* Test results */}
              {(testResults || testsLoading) && (
                <TestResults results={testResults} loading={testsLoading} />
              )}
            </div>

            {/* Right: Controls + Analysis (1/3) */}
            <div className="flex flex-col gap-4">
              <ShockInjector onShockInjected={handleShockFromInjector} />
              <AnalysisPanel
                analysis={analysis}
                riskAnalysis={riskResult}
                loading={analysisLoading}
                onRunAnalysis={handleRunAnalysis}
              />
            </div>
          </div>

          {/* Event log at bottom */}
          <div className="px-4 pb-3">
            <EventLog entries={eventLog} onClear={clearEvents} />
          </div>
        </div>
      </div>
    </CopilotSidebar>
  );
}
