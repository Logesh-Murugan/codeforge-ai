"use client";

import React, { useState } from "react";

interface ReportsViewerProps {
  reports: Record<string, string>;
}

export const ReportsViewer: React.FC<ReportsViewerProps> = ({ reports }) => {
  const reportKeys = Object.keys(reports);
  const [activeTab, setActiveTab] = useState<string>(reportKeys[0] || "validation_summary.md");

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mt-6">
      <h3 className="text-lg font-bold text-white mb-4">Generated Inspection Reports</h3>

      <div className="flex space-x-2 border-b border-slate-800 pb-2 overflow-x-auto">
        {reportKeys.map((key) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`text-xs px-3 py-1.5 rounded font-semibold whitespace-nowrap transition ${
              activeTab === key
                ? "bg-blue-600 text-white"
                : "bg-slate-800 text-slate-400 hover:bg-slate-700"
            }`}
          >
            {key}
          </button>
        ))}
      </div>

      <div className="mt-4 bg-slate-950 p-4 rounded-lg border border-slate-800 text-xs font-mono text-slate-300 max-h-72 overflow-y-auto whitespace-pre-wrap">
        {reports[activeTab] || "No report content available."}
      </div>
    </div>
  );
};
