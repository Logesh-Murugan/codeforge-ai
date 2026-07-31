"use client";

import React from "react";

interface Props {
  projectId: number;
}

export default function ContextScores({ projectId }: Props) {
  const scores = [
    { label: "Relevancy Score", val: "96%", color: "text-emerald-400" },
    { label: "Confidence Score", val: "95%", color: "text-blue-400" },
    { label: "Priority Score", val: "90%", color: "text-purple-400" },
    { label: "Freshness Score", val: "98%", color: "text-teal-400" },
    { label: "Source Score", val: "95%", color: "text-indigo-400" },
    { label: "Overall Quality Score", val: "94.8%", color: "text-amber-400" },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-100 shadow-2xl">
      <h3 className="text-md font-bold text-emerald-400 mb-4 flex items-center gap-2">
        <span>⭐</span> 6-Tier Context Quality Scores
      </h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        {scores.map((s, idx) => (
          <div key={idx} className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/60 text-center">
            <div className="text-[11px] text-slate-400">{s.label}</div>
            <div className={`text-xl font-bold mt-1 ${s.color}`}>{s.val}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
