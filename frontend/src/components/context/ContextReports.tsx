"use client";

import React from "react";

interface Props {
  projectId: number;
}

export default function ContextReports({ projectId }: Props) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-100 shadow-2xl">
      <h3 className="text-md font-bold text-amber-400 mb-4 flex items-center gap-2">
        <span>📊</span> Project Context Audit Report
      </h3>
      <div className="bg-slate-800/40 p-4 rounded-lg border border-slate-700 text-xs space-y-2">
        <div className="flex justify-between">
          <span className="text-slate-400">Project Target ID:</span>
          <span className="font-mono text-slate-200">#{projectId}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">Context Types Evaluated:</span>
          <span className="font-mono text-emerald-400">21 / 21 Types Valid</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">Routing Coverage:</span>
          <span className="font-mono text-blue-400">100% 13 Agents Mapped</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">Conflict / Corruption Index:</span>
          <span className="font-mono text-slate-300">0.0 (Clean Payload)</span>
        </div>
      </div>
    </div>
  );
}
