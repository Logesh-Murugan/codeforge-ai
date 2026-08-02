"use client";

import React from "react";

interface ProgressStats {
  overall_progress_pct: number;
  current_stage: string;
  completed_stages_count: number;
  total_stages_count: number;
  avg_agent_runtime_ms: number;
  avg_validation_score: number;
}

interface TimelineStatisticsProps {
  stats: ProgressStats;
}

export const TimelineStatistics: React.FC<TimelineStatisticsProps> = ({ stats }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
      <h3 className="text-lg font-bold text-white mb-4">Lifecycle Statistics</h3>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-xs text-slate-400 block mb-1">Completed Stages</span>
          <span className="text-xl font-bold text-white">{stats.completed_stages_count} / {stats.total_stages_count}</span>
        </div>
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-xs text-slate-400 block mb-1">Overall Progress</span>
          <span className="text-xl font-bold text-blue-400">{stats.overall_progress_pct.toFixed(0)}%</span>
        </div>
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-xs text-slate-400 block mb-1">Avg Agent Runtime</span>
          <span className="text-xl font-bold text-indigo-400">{stats.avg_agent_runtime_ms.toFixed(0)}ms</span>
        </div>
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-xs text-slate-400 block mb-1">Avg Validation Score</span>
          <span className="text-xl font-bold text-emerald-400">{(stats.avg_validation_score * 100).toFixed(0)}%</span>
        </div>
      </div>
    </div>
  );
};
