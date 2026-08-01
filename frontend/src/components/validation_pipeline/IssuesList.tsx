"use client";

import React, { useState } from "react";

interface Issue {
  title: str;
  description: str;
  severity: "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  location?: string;
  file_path?: string;
  line_number?: number;
  recommendation?: string;
}

interface IssuesListProps {
  issues: Issue[];
}

export const IssuesList: React.FC<IssuesListProps> = ({ issues }) => {
  const [filterSeverity, setFilterSeverity] = useState<string>("ALL");

  const filtered = issues.filter(
    (i) => filterSeverity === "ALL" || i.severity === filterSeverity
  );

  const getSeverityBadge = (s: string) => {
    switch (s) {
      case "CRITICAL":
        return "bg-red-500/20 text-red-300 border-red-500/40";
      case "HIGH":
        return "bg-amber-500/20 text-amber-300 border-amber-500/40";
      case "MEDIUM":
        return "bg-yellow-500/20 text-yellow-300 border-yellow-500/40";
      case "LOW":
        return "bg-blue-500/20 text-blue-300 border-blue-500/40";
      default:
        return "bg-slate-700 text-slate-300 border-slate-600";
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mt-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-white">Validation Issues ({issues.length})</h3>

        <select
          value={filterSeverity}
          onChange={(e) => setFilterSeverity(e.target.value)}
          className="bg-slate-800 border border-slate-700 text-xs text-white px-3 py-1.5 rounded focus:outline-none"
        >
          <option value="ALL">All Severities</option>
          <option value="CRITICAL">Critical Only</option>
          <option value="HIGH">High Only</option>
          <option value="MEDIUM">Medium Only</option>
          <option value="LOW">Low Only</option>
        </select>
      </div>

      <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
        {filtered.length === 0 ? (
          <div className="text-slate-500 text-xs italic">No validation issues matching selected filter.</div>
        ) : (
          filtered.map((issue, idx) => (
            <div key={idx} className="bg-slate-800/40 p-4 rounded-lg border border-slate-700/50 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-white">{issue.title}</span>
                <span className={`text-[10px] px-2 py-0.5 rounded border font-bold uppercase ${getSeverityBadge(issue.severity)}`}>
                  {issue.severity}
                </span>
              </div>
              <p className="text-xs text-slate-300">{issue.description}</p>
              {issue.file_path && (
                <span className="text-[11px] font-mono text-slate-400 block">
                  File: {issue.file_path} {issue.line_number ? `(Line ${issue.line_number})` : ""}
                </span>
              )}
              {issue.recommendation && (
                <span className="text-[11px] text-indigo-300 block font-medium">
                  Recommendation: {issue.recommendation}
                </span>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
