"use client";

import React from "react";

interface StageResult {
  stage_name: str;
  passed: boolean;
  score: number;
  execution_time_ms: number;
}

interface PipelineProgressCardProps {
  stages: StageResult[];
  status: string;
}

export const PipelineProgressCard: React.FC<PipelineProgressCardProps> = ({ stages, status }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-white">12-Stage Automated Quality Gate</h2>
          <p className="text-sm text-slate-400">Sequential multi-stage verification pipeline</p>
        </div>
        <span
          className={`px-3 py-1 text-xs font-bold rounded-full uppercase tracking-wider ${
            status === "PASSED"
              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
              : status === "WARNING"
              ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
              : "bg-red-500/10 text-red-400 border border-red-500/20"
          }`}
        >
          {status}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {stages.map((stage, idx) => (
          <div
            key={stage.stage_name}
            className={`p-3 rounded-lg border text-center ${
              stage.passed ? "bg-slate-800/60 border-emerald-500/30" : "bg-red-950/30 border-red-500/40"
            }`}
          >
            <span className="text-[10px] text-slate-400 block font-mono">Stage #{idx + 1}</span>
            <span className="text-xs font-bold text-white block my-1 truncate">{stage.stage_name}</span>
            <span className={`text-[10px] font-semibold ${stage.passed ? "text-emerald-400" : "text-red-400"}`}>
              {stage.score.toFixed(0)}/100
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
