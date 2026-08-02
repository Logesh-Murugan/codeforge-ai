"use client";

import React from "react";

interface ValidationSummaryProps {
  score: number;
  grade: string;
  durationMs: number;
  readyForExport: boolean;
}

export const ValidationSummary: React.FC<ValidationSummaryProps> = ({ score, grade, durationMs, readyForExport }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mt-6">
      <h3 className="text-lg font-bold text-white mb-4">Export Quality Readiness Summary</h3>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-xs text-slate-400 block mb-1">Quality Grade</span>
          <span className="text-xl font-bold text-emerald-400">{grade}</span>
        </div>
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-xs text-slate-400 block mb-1">Weighted Score</span>
          <span className="text-xl font-bold text-white">{score.toFixed(1)} / 100</span>
        </div>
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-xs text-slate-400 block mb-1">Execution Time</span>
          <span className="text-xl font-bold text-blue-400">{(durationMs / 1000).toFixed(2)}s</span>
        </div>
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-xs text-slate-400 block mb-1">Export Ready</span>
          <span className={`text-xl font-bold ${readyForExport ? "text-emerald-400" : "text-red-400"}`}>
            {readyForExport ? "YES ✅" : "NO ❌"}
          </span>
        </div>
      </div>
    </div>
  );
};
