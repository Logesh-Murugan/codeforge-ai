"use client";

import React from "react";

interface PerformanceMetrics {
  total_execution_time_ms: number;
  avg_agent_runtime_ms: number;
  workflow_runtime_ms: number;
  total_retries: number;
  success_rate_pct: number;
  failure_rate_pct: number;
  token_estimate: number;
  generated_files_count: number;
  current_provider: string;
  current_model: string;
  current_embedding: string;
}

interface PerformanceDashboardProps {
  metrics: PerformanceMetrics;
}

export const PerformanceDashboard: React.FC<PerformanceDashboardProps> = ({ metrics }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mt-6">
      <h3 className="text-lg font-bold text-white mb-4">Performance & Resource Observability</h3>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-slate-800/40 p-4 rounded-lg border border-slate-700/40">
          <span className="text-xs text-slate-400 block mb-1">Average Agent Runtime</span>
          <span className="text-lg font-bold text-white">{metrics.avg_agent_runtime_ms}ms</span>
        </div>

        <div className="bg-slate-800/40 p-4 rounded-lg border border-slate-700/40">
          <span className="text-xs text-slate-400 block mb-1">Success / Failure Rate</span>
          <span className="text-lg font-bold text-emerald-400">{metrics.success_rate_pct}% / {metrics.failure_rate_pct}%</span>
        </div>

        <div className="bg-slate-800/40 p-4 rounded-lg border border-slate-700/40">
          <span className="text-xs text-slate-400 block mb-1">Token Estimate</span>
          <span className="text-lg font-bold text-blue-400">{metrics.token_estimate.toLocaleString()}</span>
        </div>

        <div className="bg-slate-800/40 p-4 rounded-lg border border-slate-700/40">
          <span className="text-xs text-slate-400 block mb-1">AI Provider & Model</span>
          <span className="text-xs font-semibold text-indigo-300 block truncate">{metrics.current_provider.toUpperCase()} : {metrics.current_model}</span>
        </div>
      </div>
    </div>
  );
};
