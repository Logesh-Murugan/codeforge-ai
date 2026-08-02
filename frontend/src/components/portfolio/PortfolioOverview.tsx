"use client";

import React from "react";

interface PortfolioOverviewProps {
  summary: string;
  vision: string;
  problem: string;
  objectives: string[];
}

export const PortfolioOverview: React.FC<PortfolioOverviewProps> = ({ summary, vision, problem, objectives }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
      <div>
        <h2 className="text-xl font-bold text-white mb-2">Executive Summary</h2>
        <p className="text-sm text-slate-300 leading-relaxed">{summary}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-slate-800 pt-4">
        <div>
          <h3 className="text-sm font-semibold text-blue-400 mb-1">Project Vision</h3>
          <p className="text-xs text-slate-300">{vision}</p>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-indigo-400 mb-1">Problem Statement</h3>
          <p className="text-xs text-slate-300">{problem}</p>
        </div>
      </div>

      <div className="border-t border-slate-800 pt-4">
        <h3 className="text-sm font-semibold text-emerald-400 mb-2">Key Objectives</h3>
        <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
          {objectives.map((obj, i) => (
            <li key={i}>{obj}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};
