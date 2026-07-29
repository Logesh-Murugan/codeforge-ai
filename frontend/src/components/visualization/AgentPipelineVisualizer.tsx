"use client";

import { useState, useEffect, useCallback } from "react";

type AgentStatus = "running" | "waiting" | "completed" | "failed" | "retrying" | "skipped";

interface AgentNode {
  name: string;
  role: string;
  status: AgentStatus;
  executionTime?: number;
  retryCount?: number;
  memoryUsed?: number;
  generatedFiles?: number;
  contextInjected?: boolean;
  validationStatus?: string;
  securityScore?: number;
  documentationScore?: number;
}

const DEFAULT_AGENTS: AgentNode[] = [
  { name: "Project Manager", role: "project_manager", status: "waiting" },
  { name: "Business Analyst", role: "business_analyst", status: "waiting" },
  { name: "Product Owner", role: "product_owner", status: "waiting" },
  { name: "Solution Architect", role: "solution_architect", status: "waiting" },
  { name: "Database Engineer", role: "database_engineer", status: "waiting" },
  { name: "API Designer", role: "api_designer", status: "waiting" },
  { name: "Backend Developer", role: "backend_developer", status: "waiting" },
  { name: "Security Engineer", role: "security_engineer", status: "waiting" },
  { name: "QA Engineer", role: "qa_engineer", status: "waiting" },
  { name: "Frontend Developer", role: "frontend_developer", status: "waiting" },
  { name: "Code Reviewer", role: "code_reviewer", status: "waiting" },
  { name: "Documentation Writer", role: "documentation_writer", status: "waiting" },
  { name: "DevOps Engineer", role: "devops_engineer", status: "waiting" },
];

const STATUS_ICONS: Record<AgentStatus, string> = {
  running:     "\u23f3",
  waiting:     "\u23ed\ufe0f",
  completed:   "\u2705",
  failed:      "\u274c",
  retrying:    "\ud83d\udd04",
  skipped:     "\u23ed\ufe0f",
};

const STATUS_COLORS: Record<AgentStatus, string> = {
  running:     "border-yellow-500/50 bg-yellow-500/10",
  waiting:     "border-gray-600 bg-gray-800/40",
  completed:   "border-green-500/50 bg-green-500/10",
  failed:      "border-red-500/50 bg-red-500/10",
  retrying:    "border-orange-500/50 bg-orange-500/10",
  skipped:     "border-gray-600 bg-gray-800/20",
};

interface AgentPipelineVisualizerProps {
  agents?: AgentNode[];
  darkMode?: boolean;
}

export default function AgentPipelineVisualizer({
  agents: initialAgents,
  darkMode = true,
}: AgentPipelineVisualizerProps) {
  const [agents, setAgents] = useState<AgentNode[]>(initialAgents || DEFAULT_AGENTS);
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);
  const [currentIndex, setCurrentIndex] = useState(-1);

  const bgClass = darkMode ? "bg-gray-950 text-gray-100" : "bg-white text-gray-900";
  const panelBg = darkMode ? "bg-gray-900 border-gray-800" : "bg-gray-50 border-gray-200";
  const textMuted = darkMode ? "text-gray-400" : "text-gray-500";
  const textAccent = darkMode ? "text-indigo-400" : "text-indigo-600";
  const inputBg = darkMode ? "bg-gray-800 border-gray-700 text-gray-100" : "bg-white border-gray-300 text-gray-900";

  const advancePipeline = useCallback(() => {
    setCurrentIndex((prev) => {
      const next = prev + 1;
      if (next >= agents.length) return prev;
      setAgents((prevAgents) =>
        prevAgents.map((a, i) => {
          if (i === next) return { ...a, status: "running" as AgentStatus };
          if (i < next) return { ...a, status: "completed" as AgentStatus };
          return a;
        })
      );
      return next;
    });
  }, [agents.length]);

  useEffect(() => {
    if (currentIndex >= 0 && currentIndex < agents.length) {
      const timer = setTimeout(() => {
        setAgents((prev) =>
          prev.map((a, i) => {
            if (i === currentIndex) {
              const completed = Math.random() > 0.15;
              return {
                ...a,
                status: completed ? ("completed" as AgentStatus) : ("failed" as AgentStatus),
                executionTime: Math.round(Math.random() * 10 * 10) / 10,
                retryCount: completed ? 0 : Math.floor(Math.random() * 3) + 1,
                memoryUsed: Math.round(Math.random() * 50 * 10) / 10,
                generatedFiles: Math.floor(Math.random() * 12),
                contextInjected: true,
                validationStatus: completed ? "pass" : "fail",
                securityScore: Math.round(Math.random() * 30 + 70),
                documentationScore: Math.round(Math.random() * 30 + 70),
              };
            }
            return a;
          })
        );
        setTimeout(advancePipeline, 400);
      }, Math.random() * 1500 + 500);
      return () => clearTimeout(timer);
    }
  }, [currentIndex, advancePipeline, agents.length]);

  const handleStart = () => {
    setAgents(DEFAULT_AGENTS.map((a) => ({ ...a, status: "waiting" as AgentStatus })));
    setCurrentIndex(-1);
    setTimeout(() => advancePipeline(), 500);
  };

  const handleReset = () => {
    setAgents(DEFAULT_AGENTS.map((a) => ({ ...a, status: "waiting" as AgentStatus })));
    setCurrentIndex(-1);
    setExpandedAgent(null);
  };

  const completed = agents.filter((a) => a.status === "completed").length;
  const failed = agents.filter((a) => a.status === "failed").length;
  const running = agents.filter((a) => a.status === "running").length;

  return (
    <div className={`w-full max-w-6xl mx-auto ${bgClass} rounded-2xl shadow-2xl border p-6 ${panelBg}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-4">
        <div>
          <h2 className="text-xl font-bold">Agent Pipeline</h2>
          <p className={`text-sm ${textMuted}`}>
            {running > 0 && `${running} running \u00b7 `}
            {completed} completed \u00b7 {failed} failed \u00b7 {agents.length - completed - failed - running} pending
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleStart}
            disabled={running > 0}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg text-sm font-semibold transition-all"
          >
            Start Pipeline
          </button>
          <button
            onClick={handleReset}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all border ${darkMode ? "border-gray-700 hover:bg-gray-800" : "border-gray-300 hover:bg-gray-100"}`}
          >
            Reset
          </button>
        </div>
      </div>

      {/* Progress bar */}
      <div className="w-full h-2 bg-gray-700 rounded-full mb-6 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
          style={{ width: `${(completed / agents.length) * 100}%` }}
        />
      </div>

      {/* Agent pipeline */}
      <div className="space-y-2">
        {agents.map((agent, i) => (
          <div key={agent.role}>
            <div
              className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all hover:opacity-90 ${STATUS_COLORS[agent.status]} ${panelBg}`}
              onClick={() => setExpandedAgent(expandedAgent === agent.role ? null : agent.role)}
            >
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold flex-shrink-0 ${
                agent.status === "completed" ? "bg-green-500/20 text-green-400" :
                agent.status === "failed"   ? "bg-red-500/20 text-red-400" :
                agent.status === "running"  ? "bg-yellow-500/20 text-yellow-400" :
                                              "bg-gray-700 text-gray-500"
              }`}>
                {i + 1}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-sm">{agent.name}</div>
                <div className={`text-xs ${textMuted}`}>{agent.role.replace(/_/g, " ")}</div>
              </div>
              <div className="flex items-center gap-3 text-xs">
                {agent.executionTime && (
                  <span className={textMuted}>{agent.executionTime.toFixed(1)}s</span>
                )}
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                  agent.status === "completed" ? "bg-green-500/20 text-green-400" :
                  agent.status === "failed"    ? "bg-red-500/20 text-red-400" :
                  agent.status === "running"   ? "bg-yellow-500/20 text-yellow-400 animate-pulse" :
                  agent.status === "retrying"  ? "bg-orange-500/20 text-orange-400" :
                                                  "bg-gray-700 text-gray-500"
                }`}>
                  {STATUS_ICONS[agent.status]} {agent.status}
                </span>
              </div>
            </div>

            {/* Expanded details */}
            {expandedAgent === agent.role && agent.status !== "waiting" && (
              <div className={`ml-11 p-4 rounded-xl border mt-1 ${panelBg}`}>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                  {agent.executionTime !== undefined && (
                    <div>
                      <span className={textMuted}>Exec Time</span>
                      <div className="font-semibold">{agent.executionTime.toFixed(1)}s</div>
                    </div>
                  )}
                  {agent.retryCount !== undefined && (
                    <div>
                      <span className={textMuted}>Retries</span>
                      <div className="font-semibold">{agent.retryCount}</div>
                    </div>
                  )}
                  {agent.memoryUsed !== undefined && (
                    <div>
                      <span className={textMuted}>Memory</span>
                      <div className="font-semibold">{agent.memoryUsed.toFixed(1)} KB</div>
                    </div>
                  )}
                  {agent.generatedFiles !== undefined && (
                    <div>
                      <span className={textMuted}>Files</span>
                      <div className="font-semibold">{agent.generatedFiles}</div>
                    </div>
                  )}
                  {agent.contextInjected !== undefined && (
                    <div>
                      <span className={textMuted}>Context</span>
                      <div className="font-semibold">{agent.contextInjected ? "Injected" : "None"}</div>
                    </div>
                  )}
                  {agent.validationStatus && (
                    <div>
                      <span className={textMuted}>Validation</span>
                      <div className={`font-semibold ${agent.validationStatus === "pass" ? "text-green-400" : "text-red-400"}`}>
                        {agent.validationStatus.toUpperCase()}
                      </div>
                    </div>
                  )}
                  {agent.securityScore !== undefined && (
                    <div>
                      <span className={textMuted}>Security</span>
                      <div className="font-semibold">{agent.securityScore}/100</div>
                    </div>
                  )}
                  {agent.documentationScore !== undefined && (
                    <div>
                      <span className={textMuted}>Docs</span>
                      <div className="font-semibold">{agent.documentationScore}/100</div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
