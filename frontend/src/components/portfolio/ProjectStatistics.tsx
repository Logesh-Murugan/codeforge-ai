"use client";

import React from "react";

interface ProjectStatisticsProps {
  metrics: any;
}

export const ProjectStatistics: React.FC<ProjectStatisticsProps> = ({ metrics }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mt-6">
      <h3 className="text-lg font-bold text-white mb-4">Project Statistics & Telemetry</h3>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center text-xs">
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-slate-400 block mb-1">Deployment Readiness</span>
          <span className="font-bold text-emerald-400 text-sm">{metrics.deployment_readiness}</span>
        </div>
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-slate-400 block mb-1">Quality Grade</span>
          <span className="font-bold text-white text-sm">{metrics.quality_grade}</span>
        </div>
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-slate-400 block mb-1">Security Checks</span>
          <span className="font-bold text-cyan-400 text-sm">{metrics.security_checks_passed} Passed</span>
        </div>
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-slate-400 block mb-1">Execution Duration</span>
          <span className="font-bold text-indigo-400 text-sm">{(metrics.total_execution_duration_ms / 1000).toFixed(1)}s</span>
        </div>
      </div>
    </div>
  );
};
