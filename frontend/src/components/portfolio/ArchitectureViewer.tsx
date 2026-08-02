"use client";

import React, { useState } from "react";

interface ArchitectureViewerProps {
  architecture: Record<string, string>;
  diagrams: Record<string, string>;
}

export const ArchitectureViewer: React.FC<ArchitectureViewerProps> = ({ architecture, diagrams }) => {
  const [activeTab, setActiveTab] = useState<string>("system_architecture");
  const [viewDiagrams, setViewDiagrams] = useState<boolean>(false);

  const keys = viewDiagrams ? Object.keys(diagrams) : Object.keys(architecture);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mt-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-white">System Architecture & Mermaid Diagrams</h3>
        <button
          onClick={() => {
            setViewDiagrams(!viewDiagrams);
            setActiveTab(viewDiagrams ? "system_architecture" : "flowchart");
          }}
          className="text-xs bg-blue-600 hover:bg-blue-500 text-white font-semibold px-3 py-1.5 rounded transition"
        >
          {viewDiagrams ? "View Text Docs" : "View Mermaid Diagrams"}
        </button>
      </div>

      <div className="flex space-x-2 border-b border-slate-800 pb-2 overflow-x-auto">
        {keys.map((k) => (
          <button
            key={k}
            onClick={() => setActiveTab(k)}
            className={`text-xs px-3 py-1 rounded font-semibold whitespace-nowrap transition ${
              activeTab === k ? "bg-blue-600 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"
            }`}
          >
            {k.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      <div className="mt-4 bg-slate-950 p-4 rounded-lg border border-slate-800 text-xs font-mono text-slate-300 max-h-72 overflow-y-auto whitespace-pre-wrap">
        {viewDiagrams ? diagrams[activeTab] || "No diagram available." : architecture[activeTab] || "No doc content."}
      </div>
    </div>
  );
};
