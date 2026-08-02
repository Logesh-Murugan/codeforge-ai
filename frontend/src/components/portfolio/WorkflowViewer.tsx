"use client";

import React from "react";

interface AgentWorkflow {
  agent_name: string;
  responsibilities: string;
  execution_time_ms: number;
  generated_artifacts: string[];
  validation_status: string;
}

interface WorkflowViewerProps {
  workflows: AgentWorkflow[];
}

export const WorkflowViewer: React.FC<WorkflowViewerProps> = ({ workflows }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mt-6">
      <h3 className="text-lg font-bold text-white mb-4">13-Agent AI Collaboration Workflow</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {workflows.map((wf, i) => (
          <div key={i} className="bg-slate-800/40 p-4 rounded-lg border border-slate-700/40 space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-bold text-white uppercase">{wf.agent_name.replace(/_/g, " ")}</span>
              <span className="text-[10px] px-2 py-0.5 rounded font-bold bg-emerald-500/20 text-emerald-300">
                {wf.validation_status}
              </span>
            </div>
            <p className="text-slate-300">{wf.responsibilities}</p>
            <div className="flex justify-between items-center text-[10px] text-slate-400 font-mono">
              <span>{wf.execution_time_ms}ms</span>
              <span>Files: {wf.generated_artifacts.length}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
