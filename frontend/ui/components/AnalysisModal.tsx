"use client";

import { useAEX } from "@/lib/store";
import { X, Brain, Clock, Hash, Cpu } from "lucide-react";

export function AnalysisModal() {
  const { analysisOpen, analysisResult, closeAnalysis } = useAEX();

  if (!analysisOpen || !analysisResult) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={closeAnalysis} />

      {/* Modal */}
      <div className="relative glass-card w-full max-w-lg mx-4 animate-slide-up max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border-subtle">
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-accent" />
            <span className="text-sm font-semibold text-white">Bedrock Market Analysis</span>
          </div>
          <button onClick={closeAnalysis} className="p-1 rounded-md hover:bg-surface-3/60 transition-colors">
            <X className="w-4 h-4 text-gray-400" />
          </button>
        </div>

        {/* Meta */}
        <div className="flex items-center gap-3 px-4 py-2 border-b border-border-subtle text-[10px] font-mono text-gray-500">
          <span className="flex items-center gap-1"><Hash className="w-3 h-3" /> {analysisResult.runId}</span>
          <span className="flex items-center gap-1"><Cpu className="w-3 h-3" /> {analysisResult.tokens} tokens</span>
          <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {analysisResult.latencyMs}ms</span>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-4 py-3">
          <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
            {analysisResult.text}
          </div>
        </div>

        {/* Footer */}
        <div className="px-4 py-2.5 border-t border-border-subtle flex justify-end">
          <button onClick={closeAnalysis} className="btn-primary text-xs">Close</button>
        </div>
      </div>
    </div>
  );
}
