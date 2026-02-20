"use client";

import { useState } from "react";
import type { AnalysisResult, RiskResult } from "../types/market";
import { fetchAudioSummary } from "../lib/api";

interface AnalysisPanelProps {
  analysis: AnalysisResult | null;
  riskAnalysis: RiskResult | null;
  loading: boolean;
  onRunAnalysis: (question?: string) => void;
}

const RISK_COLORS: Record<string, string> = {
  LOW:      "bg-green-900/40 text-green-300 border-green-700",
  MEDIUM:   "bg-yellow-900/40 text-yellow-300 border-yellow-700",
  HIGH:     "bg-orange-900/40 text-orange-300 border-orange-700",
  CRITICAL: "bg-red-900/40 text-red-300 border-red-700",
};

export function AnalysisPanel({ analysis, riskAnalysis, loading, onRunAnalysis }: AnalysisPanelProps) {
  const [audioLoading, setAudioLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [customQuestion, setCustomQuestion] = useState("");

  async function handlePlayAudio() {
    if (!analysis?.text) return;
    setAudioLoading(true);
    try {
      const { audio_url } = await fetchAudioSummary(analysis.text.slice(0, 500));
      setAudioUrl(audio_url);
    } catch (e) {
      console.warn("Audio unavailable", e);
    } finally {
      setAudioLoading(false);
    }
  }

  function handleSubmitQuestion(e: React.FormEvent) {
    e.preventDefault();
    if (customQuestion.trim()) {
      onRunAnalysis(customQuestion.trim());
      setCustomQuestion("");
    }
  }

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 flex flex-col gap-4">
      <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
        Bedrock Market Analysis
      </h3>

      {/* Custom question */}
      <form onSubmit={handleSubmitQuestion} className="flex gap-2">
        <input
          type="text"
          value={customQuestion}
          onChange={e => setCustomQuestion(e.target.value)}
          placeholder='Ask: "Why did CompliBot pump?"'
          className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-3 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
        />
        <button
          type="submit"
          disabled={loading || !customQuestion.trim()}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg disabled:opacity-50 transition-colors"
        >
          Ask
        </button>
      </form>

      {/* Risk level badge */}
      {riskAnalysis && (
        <div className={`px-3 py-2 rounded-lg border text-sm font-semibold ${RISK_COLORS[riskAnalysis.risk_level]}`}>
          Risk Level: {riskAnalysis.risk_level}
        </div>
      )}

      {/* Analysis text */}
      {loading && (
        <div className="flex items-center gap-2 text-blue-400 text-sm">
          <span className="animate-spin text-lg">⟳</span> Thinking...
        </div>
      )}

      {analysis && !loading && (
        <div className="flex flex-col gap-2">
          <div className="bg-gray-900/60 rounded-lg p-3 text-sm text-gray-200 leading-relaxed whitespace-pre-wrap max-h-64 overflow-y-auto">
            {analysis.text}
          </div>
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>
              {analysis.model.split(".").pop()} · {analysis.input_tokens + analysis.output_tokens} tokens · {analysis.latency_ms}ms
              {analysis.cached && " · (cached)"}
            </span>
            <button
              onClick={handlePlayAudio}
              disabled={audioLoading}
              className="text-purple-400 hover:text-purple-300 transition-colors disabled:opacity-50"
            >
              {audioLoading ? "Loading audio..." : "▶ Play Audio"}
            </button>
          </div>

          {audioUrl && (
            <audio
              controls
              src={audioUrl}
              autoPlay
              className="w-full h-8 mt-1"
            />
          )}
        </div>
      )}

      {/* Risk analysis */}
      {riskAnalysis && !loading && (
        <div className="bg-gray-900/60 rounded-lg p-3 text-sm text-gray-300 leading-relaxed whitespace-pre-wrap max-h-40 overflow-y-auto border-t border-gray-700 mt-1">
          <p className="text-xs text-gray-500 mb-1 font-semibold uppercase">Risk Assessment</p>
          {riskAnalysis.text}
        </div>
      )}

      {!analysis && !loading && (
        <div className="text-center text-gray-500 text-sm py-4">
          Click <strong>Run Analysis</strong> or ask a question above
        </div>
      )}
    </div>
  );
}
