"use client";

import type { TestResults as TestResultsType } from "../types/market";

interface TestResultsProps {
  results: TestResultsType | null;
  loading: boolean;
}

export function TestResults({ results, loading }: TestResultsProps) {
  if (loading) {
    return (
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <div className="flex items-center gap-2 text-purple-400 text-sm">
          <span className="animate-spin">⟳</span> Running TestSprite tests...
        </div>
      </div>
    );
  }

  if (!results) return null;

  const allPassed = results.results.every(r => r.status === "PASS");

  return (
    <div className={`border rounded-xl p-4 ${allPassed ? "bg-green-900/20 border-green-700" : "bg-red-900/20 border-red-700"}`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">TestSprite Results</h3>
        <span className={`text-sm font-bold ${allPassed ? "text-green-400" : "text-red-400"}`}>
          {results.summary}
        </span>
      </div>
      <div className="space-y-2">
        {results.results.map(result => (
          <div
            key={result.test_name}
            className={`p-3 rounded-lg border ${result.status === "PASS" ? "bg-green-900/30 border-green-700" : "bg-red-900/30 border-red-700"}`}
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-white">
                {result.status === "PASS" ? "✓" : "✗"} {result.test_name.replace(/_/g, " ")}
              </span>
              <span className="text-xs text-gray-400">{result.duration_ms}ms</span>
            </div>
            {result.status === "PASS" && result.test_name === "inflow_price_rule" && (
              <p className="text-xs text-green-300 mt-1">
                Price: ${(result.details as any).price_before} → ${(result.details as any).price_after}
                {" "}(+{(result.details as any).price_change_pct}%)
              </p>
            )}
            {result.status === "PASS" && result.test_name === "shock_sector_rule" && (
              <p className="text-xs text-green-300 mt-1">
                Compliance: +{(result.details as any).compliance_avg_change_pct}%,
                {" "}Fraud/AML: {(result.details as any).fraud_aml_avg_change_pct}%,
                {" "}spread: {(result.details as any).spread_pct}%
              </p>
            )}
            {result.status === "FAIL" && (
              <p className="text-xs text-red-300 mt-1">{result.error ?? "Assertion failed"}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
