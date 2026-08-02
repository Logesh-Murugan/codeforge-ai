"use client";

import React from "react";

interface StageResult {
  stage_name: string;
  passed: boolean;
  score: number;
}

interface ValidationProgressProps {
  stages: StageResult[];
  status: string;
}

export const ValidationProgress: React.FC<ValidationProgressProps> = ({ stages, status }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-white">Validation Pipeline Progress</h2>
          <p className="text-sm text-slate-400">Sequential multi-stage verification pipeline</p>
        </div>
        <span className="px-3 py-1 text-xs font-bold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase">
          {status}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {stages.map((stg, i) => (
          <div key={i} className="p-3 rounded-lg bg-slate-800/60 border border-slate-700/50 text-center">
            <span className="text-[10px] text-slate-400 font-mono block">Stage #{i + 1}</span>
            <span className="text-xs font-bold text-white block truncate my-1">{stg.stage_name}</span>
            <span className="text-[10px] font-semibold text-emerald-400">{stg.score.toFixed(0)}/100</span>
          </div>
        ))}
      </div>
    </div>
  );
};
