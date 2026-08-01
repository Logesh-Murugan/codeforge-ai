"use client";

import React from "react";

interface AgentExecution {
  agent_name: str;
  status: "waiting" | "running" | "retrying" | "completed" | "failed" | "cancelled";
  execution_time_ms: number;
  retry_count: number;
  current_task?: string;
  generated_files_count: number;
  validation_score: number;
}

interface AgentPipelineViewProps {
  agents: AgentExecution[];
}

const AGENT_LABELS: Record<string, string> = {
  project_manager: "Project Manager",
  business_analyst: "Business Analyst",
  product_owner: "Product Owner",
  solution_architect: "Solution Architect",
  database_engineer: "Database Engineer",
  api_designer: "API Designer",
  backend_developer: "Backend Developer",
  security_engineer: "Security Engineer",
  qa_engineer: "QA Engineer",
  frontend_developer: "Frontend Developer",
  code_reviewer: "Code Reviewer",
  documentation_writer: "Documentation Writer",
  devops_engineer: "DevOps Engineer",
};

export const AgentPipelineView: React.FC<AgentPipelineViewProps> = ({ agents }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mt-6">
      <h3 className="text-lg font-bold text-white mb-4">13-Agent Execution Pipeline</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {agents.map((agent, index) => {
          const isCompleted = agent.status === "completed";
          const isRunning = agent.status === "running";
          const isRetrying = agent.status === "retrying";

          return (
            <div
              key={agent.agent_name}
              className={`p-4 rounded-lg border transition-all ${
                isCompleted
                  ? "bg-slate-800/80 border-emerald-500/30"
                  : isRunning
                  ? "bg-blue-950/40 border-blue-500 animate-pulse shadow-lg shadow-blue-500/10"
                  : isRetrying
                  ? "bg-amber-950/40 border-amber-500"
                  : "bg-slate-800/20 border-slate-700/50 opacity-60"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-400">Step #{index + 1}</span>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                    isCompleted
                      ? "bg-emerald-500/20 text-emerald-300"
                      : isRunning
                      ? "bg-blue-500/20 text-blue-300"
                      : "bg-slate-700 text-slate-400"
                  }`}
                >
                  {agent.status}
                </span>
              </div>

              <h4 className="font-semibold text-white text-sm mb-2">
                {AGENT_LABELS[agent.agent_name] || agent.agent_name}
              </h4>

              <div className="space-y-1 text-xs text-slate-400">
                <div className="flex justify-between">
                  <span>Runtime:</span>
                  <span className="text-slate-200">{agent.execution_time_ms}ms</span>
                </div>
                <div className="flex justify-between">
                  <span>Files Generated:</span>
                  <span className="text-slate-200">{agent.generated_files_count}</span>
                </div>
                <div className="flex justify-between">
                  <span>Validation Score:</span>
                  <span className="text-emerald-400">{(agent.validation_score * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
