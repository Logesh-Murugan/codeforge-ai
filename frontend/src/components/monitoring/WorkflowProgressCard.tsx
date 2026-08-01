"use client";

import React from "react";

interface WorkflowProgressCardProps {
  status: {
    status: string;
    current_agent?: string;
    completed_steps: number;
    total_steps: number;
    progress_pct: number;
    execution_duration_ms: number;
    estimated_remaining_ms: number;
    retry_count: number;
  };
}

export const WorkflowProgressCard: React.FC<WorkflowProgressCardProps> = ({ status }) => {
  const isCompleted = status.status === "completed";

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">Workflow Execution Status</h2>
          <p className="text-sm text-slate-400">13-Agent LangGraph Multi-Agent Pipeline</p>
        </div>
        <span
          className={`px-3 py-1 text-xs font-semibold rounded-full uppercase tracking-wider ${
            isCompleted
              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
              : "bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse"
          }`}
        >
          {status.status}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between text-xs text-slate-400 mb-1">
          <span>Overall Progress ({status.completed_steps} / {status.total_steps} agents)</span>
          <span className="font-bold text-blue-400">{status.progress_pct}%</span>
        </div>
        <div className="w-full bg-slate-800 h-3 rounded-full overflow-hidden">
          <div
            className="bg-gradient-to-r from-blue-500 to-indigo-500 h-full transition-all duration-500 ease-out"
            style={{ width: `${status.progress_pct}%` }}
          />
        </div>
      </div>

      {/* Metric Counters */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
          <span className="text-xs text-slate-400 block">Current Active Agent</span>
          <span className="text-sm font-semibold text-white truncate block">
            {status.current_agent || (isCompleted ? "All Completed" : "Initialization")}
          </span>
        </div>

        <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
          <span className="text-xs text-slate-400 block">Execution Duration</span>
          <span className="text-sm font-semibold text-white">
            {(status.execution_duration_ms / 1000).toFixed(1)}s
          </span>
        </div>

        <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
          <span className="text-xs text-slate-400 block">Estimated Remaining</span>
          <span className="text-sm font-semibold text-white">
            {(status.estimated_remaining_ms / 1000).toFixed(1)}s
          </span>
        </div>

        <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700/50">
          <span className="text-xs text-slate-400 block">Retry Count</span>
          <span className="text-sm font-semibold text-amber-400">
            {status.retry_count}
          </span>
        </div>
      </div>
    </div>
  );
};
