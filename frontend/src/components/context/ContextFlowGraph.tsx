"use client";

import React from "react";

interface Props {
  projectId: number;
}

export default function ContextFlowGraph({ projectId }: Props) {
  const contextEdges = [
    { from: "Project", to: "Requirement", label: "defines" },
    { from: "Requirement", to: "Architecture", label: "shapes" },
    { from: "Architecture", to: "Database", label: "structures" },
    { from: "Architecture", to: "API", label: "specifies" },
    { from: "Database", to: "Backend", label: "provides_schema" },
    { from: "API", to: "Backend & Frontend", label: "contracts" },
    { from: "Backend", to: "Security & Testing", label: "evaluates" },
    { from: "Testing & QA", to: "Code Reviewer", label: "verifies" },
    { from: "Documentation", to: "DevOps & Deployment", label: "deploys" },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-100 shadow-2xl">
      <h3 className="text-md font-bold text-indigo-400 mb-4 flex items-center gap-2">
        <span>🔄</span> Context Flow Graph & Relationship Dependency Matrix
      </h3>
      <div className="space-y-3">
        {contextEdges.map((edge, idx) => (
          <div key={idx} className="flex items-center justify-between bg-slate-800/50 p-3 rounded-lg border border-slate-700 text-xs">
            <div className="flex items-center gap-2">
              <span className="px-2 py-1 bg-indigo-500/20 text-indigo-300 rounded font-semibold">{edge.from}</span>
              <span className="text-slate-500">➔ [{edge.label}] ➔</span>
              <span className="px-2 py-1 bg-emerald-500/20 text-emerald-300 rounded font-semibold">{edge.to}</span>
            </div>
            <span className="text-slate-400 font-mono text-[10px]">ACTIVE ROUTE</span>
          </div>
        ))}
      </div>
    </div>
  );
}
