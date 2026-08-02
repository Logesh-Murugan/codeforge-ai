"use client";

import React from "react";

export const EngineeringTimeline: React.FC = () => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mt-6">
      <h3 className="text-lg font-bold text-white mb-4">Engineering Lifecycle Timeline</h3>

      <div className="flex items-center space-x-2 text-xs overflow-x-auto pb-2">
        <span className="bg-slate-800 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 whitespace-nowrap">1. Requirement Scoping</span>
        <span className="text-slate-600">→</span>
        <span className="bg-slate-800 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 whitespace-nowrap">2. 13-Agent Execution</span>
        <span className="text-slate-600">→</span>
        <span className="bg-slate-800 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 whitespace-nowrap">3. 12-Stage Validation</span>
        <span className="text-slate-600">→</span>
        <span className="bg-slate-800 text-emerald-300 px-3 py-1.5 rounded-lg border border-emerald-500/30 whitespace-nowrap font-bold">4. Portfolio Ready</span>
      </div>
    </div>
  );
};
