"use client";

import React from "react";

interface ValidationHistoryItem {
  run_id: number;
  status: string;
  score: number;
  quality_grade: string;
  duration_ms: number;
  executed_at: string;
}

interface ValidationHistoryProps {
  history: ValidationHistoryItem[];
}

export const ValidationHistory: React.FC<ValidationHistoryProps> = ({ history }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mt-6">
      <h3 className="text-lg font-bold text-white mb-4">Validation Execution History</h3>

      <div className="space-y-2">
        {history.map((item) => (
          <div key={item.run_id} className="flex items-center justify-between bg-slate-800/40 p-3 rounded-lg border border-slate-700/40 text-xs">
            <span className="font-semibold text-white">Run #{item.run_id}</span>
            <span className="text-emerald-400 font-bold">{item.score.toFixed(1)}/100 ({item.quality_grade})</span>
            <span className="text-slate-400">{(item.duration_ms / 1000).toFixed(1)}s</span>
            <span className="text-slate-500 font-mono">{item.executed_at}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
