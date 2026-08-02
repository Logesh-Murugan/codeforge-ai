"use client";

import React from "react";

interface AnalyticsData {
  total_events: number;
  longest_stage?: string;
  shortest_stage?: string;
  total_retries: number;
  average_runtime_ms: number;
}

interface TimelineAnalyticsProps {
  analytics: AnalyticsData;
}

export const TimelineAnalytics: React.FC<TimelineAnalyticsProps> = ({ analytics }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mt-6">
      <h3 className="text-lg font-bold text-white mb-4">Performance Analytics Breakdown</h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-slate-400 block">Total Lifecycle Events</span>
          <span className="text-sm font-bold text-white">{analytics.total_events}</span>
        </div>
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-slate-400 block">Longest Stage</span>
          <span className="text-sm font-bold text-amber-300 truncate block">{analytics.longest_stage || "N/A"}</span>
        </div>
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-slate-400 block">Shortest Stage</span>
          <span className="text-sm font-bold text-emerald-300 truncate block">{analytics.shortest_stage || "N/A"}</span>
        </div>
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-slate-400 block">Total Retries</span>
          <span className="text-sm font-bold text-blue-300">{analytics.total_retries}</span>
        </div>
      </div>
    </div>
  );
};
