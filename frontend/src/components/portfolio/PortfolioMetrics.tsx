"use client";

import React from "react";

interface MetricsProps {
  linesOfCode: number;
  filesCount: number;
  apisCount: number;
  modelsCount: number;
  validationScore: number;
  testCoverage: number;
}

export const PortfolioMetrics: React.FC<MetricsProps> = ({
  linesOfCode,
  filesCount,
  apisCount,
  modelsCount,
  validationScore,
  testCoverage,
}) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
      <h3 className="text-lg font-bold text-white mb-4">Engineering Metrics Grid</h3>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 text-center">
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-xs text-slate-400 block mb-1">Lines of Code</span>
          <span className="text-xl font-bold text-white">{linesOfCode}</span>
        </div>
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-xs text-slate-400 block mb-1">Files Generated</span>
          <span className="text-xl font-bold text-blue-400">{filesCount}</span>
        </div>
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-xs text-slate-400 block mb-1">REST APIs</span>
          <span className="text-xl font-bold text-indigo-400">{apisCount}</span>
        </div>
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-xs text-slate-400 block mb-1">Models</span>
          <span className="text-xl font-bold text-purple-400">{modelsCount}</span>
        </div>
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-xs text-slate-400 block mb-1">Validation Score</span>
          <span className="text-xl font-bold text-emerald-400">{validationScore.toFixed(1)}/100</span>
        </div>
        <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
          <span className="text-xs text-slate-400 block mb-1">Test Coverage</span>
          <span className="text-xl font-bold text-cyan-400">{testCoverage.toFixed(1)}%</span>
        </div>
      </div>
    </div>
  );
};
