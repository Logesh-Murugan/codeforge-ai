"use client";

import React from "react";

interface Issue {
  title: string;
  description: string;
  severity: string;
  file_path?: string;
  recommendation?: string;
}

interface ValidationIssueTableProps {
  issues: Issue[];
}

export const ValidationIssueTable: React.FC<ValidationIssueTableProps> = ({ issues }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mt-6">
      <h3 className="text-lg font-bold text-white mb-4">Validation Issues & Recommendations ({issues.length})</h3>

      <div className="space-y-3 max-h-72 overflow-y-auto">
        {issues.length === 0 ? (
          <div className="text-slate-500 text-xs italic">No validation issues detected.</div>
        ) : (
          issues.map((iss, i) => (
            <div key={i} className="bg-slate-800/40 p-4 rounded-lg border border-slate-700/40 space-y-1 text-xs">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-white">{iss.title}</span>
                <span className="text-[10px] px-2 py-0.5 rounded font-bold uppercase bg-amber-500/20 text-amber-300">
                  {iss.severity}
                </span>
              </div>
              <p className="text-slate-300">{iss.description}</p>
              {iss.recommendation && (
                <span className="text-indigo-300 block font-medium">Recommendation: {iss.recommendation}</span>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
