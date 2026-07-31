"use client";

import { useEffect, useState, useMemo } from "react";

const AGENT_PIPELINE = [
  { id: "project_manager", label: "Project Manager", icon: "📋", desc: "Master plan, milestones, goals" },
  { id: "business_analyst", label: "Business Analyst", icon: "📊", desc: "Entities, actions, auth requirements" },
  { id: "product_owner", label: "Product Owner", icon: "👑", desc: "Prioritized backlog, sprint goals, MoSCoW" },
  { id: "solution_architect", label: "Solution Architect", icon: "📐", desc: "DB schema, endpoints, file structure" },
  { id: "database_engineer", label: "Database Engineer", icon: "🗄️", desc: "Indexes, relationships, migrations, SQLAlchemy" },
  { id: "api_designer", label: "API Designer", icon: "🔌", desc: "OpenAPI spec, request/response models, auth flow" },
  { id: "backend_developer", label: "Backend Developer", icon: "💻", desc: "FastAPI routes, models, schemas, business logic" },
  { id: "security_engineer", label: "Security Engineer", icon: "🔐", desc: "OWASP audit, JWT, injection, secrets, patches" },
  { id: "qa_engineer", label: "QA Engineer", icon: "🧪", desc: "Test plan, unit/integration/API tests, edge cases" },
  { id: "frontend_developer", label: "Frontend Developer", icon: "🖥️", desc: "Next.js pages, forms, React Query integration" },
  { id: "code_reviewer", label: "Code Reviewer", icon: "🛡️", desc: "Security review, style fixes, auto-fixes" },
  { id: "documentation_writer", label: "Doc Writer", icon: "📝", desc: "README, installation, API docs, deployment guide" },
  { id: "devops_engineer", label: "DevOps Engineer", icon: "🐳", desc: "Dockerfile, Compose, Nginx, CI/CD, prod config" },
];

export type AgentStatus = "waiting" | "running" | "completed" | "failed" | "retrying" | "skipped";

export interface AgentRunData {
  id: number;
  agent_name: string;
  status: AgentStatus;
  output_json: Record<string, unknown> | null;
  error_message: string | null;
  execution_time_seconds: number | null;
  retry_count: number;
  created_at: string;
  updated_at: string;
}

export interface AgentDetailData {
  execution_time: number | null;
  retry_count: number;
  generated_files: number;
  context_injected: number;
  validation_status: string;
  security_score: number;
  documentation_score: number;
}

const STATUS_CONFIG: Record<AgentStatus, { label: string; color: string; bgColor: string; icon: string }> = {
  waiting: { label: "Waiting", color: "text-gray-500", bgColor: "bg-gray-800/50", icon: "⏸️" },
  running: { label: "Running", color: "text-yellow-400", bgColor: "bg-yellow-500/10", icon: "⏳" },
  completed: { label: "Completed", color: "text-emerald-400", bgColor: "bg-emerald-500/10", icon: "✅" },
  failed: { label: "Failed", color: "text-red-400", bgColor: "bg-red-500/10", icon: "❌" },
  retrying: { label: "Retrying", color: "text-orange-400", bgColor: "bg-orange-500/10", icon: "🔄" },
  skipped: { label: "Skipped", color: "text-gray-500", bgColor: "bg-gray-800/50", icon: "⏭️" },
};

function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds === undefined) return "—";
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}m ${secs}s`;
}

function AgentNode({ agent, status, isActive, isCompleted, index, total, onClick, className = "" }: {
  agent: typeof AGENT_PIPELINE[0];
  status: AgentStatus;
  isActive: boolean;
  isCompleted: boolean;
  index: number;
  total: number;
  onClick: () => void;
  className?: string;
}) {
  const config = STATUS_CONFIG[status];
  const isLast = index === total - 1;

  return (
    <div className={`flex flex-col items-center group ${className}`} onClick={onClick}>
      <div className="relative">
        <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-2xl border-2 transition-all duration-300 ${
          isActive ? "ring-4 ring-indigo-500/50 animate-pulse" : ""
        } ${config.bgColor} border-gray-700 ${isCompleted ? "border-emerald-500/50" : ""} ${status === "failed" ? "border-red-500/50" : ""} ${status === "running" ? "border-yellow-500/50" : ""}`}>
          {agent.icon}
        </div>
        {status === "running" && (
          <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-yellow-500 border-2 border-gray-900 animate-ping" />
        )}
        {status === "completed" && (
          <div className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-emerald-500 border-2 border-gray-900 flex items-center justify-center">
            <span className="text-white text-xs">✓</span>
          </div>
        )}
        {status === "failed" && (
          <div className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-red-500 border-2 border-gray-900 flex items-center justify-center">
            <span className="text-white text-xs">✗</span>
          </div>
        )}
      </div>
      <div className="mt-2 text-center w-28">
        <p className={`text-xs font-semibold truncate ${config.color}`}>{agent.label}</p>
        <p className={`text-[10px] truncate ${config.color}`}>{config.label}</p>
        {status === "running" && (
          <div className="mt-1 w-full h-1 bg-gray-800 rounded-full overflow-hidden">
            <div className="h-full bg-indigo-500 animate-pulse" style={{ width: "100%" }} />
          </div>
        )}
      </div>
      {!isLast && (
        <div className={`w-1 h-8 mx-auto ${isCompleted ? "bg-emerald-500/50" : "bg-gray-700"} relative`}>
          <div className={`absolute top-0 left-0 w-full h-full ${isActive ? "bg-gradient-to-b from-indigo-500 to-indigo-600 animate-pulse" : ""}`} />
        </div>
      )}
    </div>
  );
}

function AgentDetailPanel({ agent, runData, detailData }: {
  agent: typeof AGENT_PIPELINE[0] | null;
  runData: AgentRunData | null;
  detailData: AgentDetailData | null;
}) {
  if (!agent || !runData) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-16 text-center text-gray-500">
        <div className="text-6xl mb-4">🤖</div>
        <h3 className="text-lg font-semibold text-white mb-2">Select an Agent</h3>
        <p className="text-sm max-w-xs">Click on any agent in the pipeline to view detailed execution metrics and outputs.</p>
      </div>
    );
  }

  const config = STATUS_CONFIG[runData.status];
  const output = runData.output_json || {};

  return (
    <div className="flex-1 overflow-y-auto space-y-6 p-6">
      <div className={`flex items-center gap-4 p-4 rounded-2xl ${config.bgColor} border border-gray-700`}>
        <span className="text-3xl">{agent.icon}</span>
        <div>
          <h3 className="text-lg font-bold text-white">{agent.label}</h3>
          <p className="text-xs text-gray-400">{agent.desc}</p>
          <span className={`inline-block mt-1 px-3 py-1 rounded-full text-xs font-semibold ${config.color} ${config.bgColor.replace("bg-", "bg-").replace("/10", "/30")}`}>
            {config.icon} {config.label}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard label="Execution Time" value={formatDuration(runData.execution_time_seconds)} icon="⏱️" />
        <MetricCard label="Retry Count" value={runData.retry_count.toString()} icon="🔄" />
        <MetricCard label="Files Generated" value={detailData?.generated_files?.toString() || "0"} icon="📄" />
        <MetricCard label="Context Injected" value={detailData?.context_injected?.toString() || "0"} icon="🧠" />
        <MetricCard label="Validation" value={detailData?.validation_status || "Pending"} icon="✅" />
        <MetricCard label="Security Score" value={`${detailData?.security_score || 0}/100`} icon="🔐" />
        <MetricCard label="Doc Score" value={`${detailData?.documentation_score || 0}/100`} icon="📝" />
        <MetricCard label="Memory Records" value={Object.keys(output).length.toString()} icon="💾" />
      </div>

      {runData.error_message && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-4">
          <div className="flex items-center gap-2 text-red-400 mb-2">
            <span>⚠️</span>
            <span className="font-semibold">Execution Error</span>
          </div>
          <pre className="text-xs text-red-300 bg-black/30 p-3 rounded-xl overflow-x-auto whitespace-pre-wrap">
            {runData.error_message}
          </pre>
        </div>
      )}

      {Object.keys(output).length > 0 && (
        <div className="space-y-4">
          <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Agent Output Summary</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-96 overflow-y-auto">
            {Object.entries(output).slice(0, 12).map(([key, value]) => (
              <div key={key} className="bg-white/5 border border-white/5 rounded-xl p-3">
                <span className="text-[10px] text-indigo-400 font-semibold uppercase tracking-wider block mb-1">{key}</span>
                <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap max-h-24 overflow-y-auto">
                  {typeof value === "object" ? JSON.stringify(value, null, 2).slice(0, 300) : String(value).slice(0, 300)}
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, icon }: { label: string; value: string; icon: string }) {
  return (
    <div className="bg-white/5 border border-white/5 rounded-2xl p-4">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">{icon}</span>
        <span className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider">{label}</span>
      </div>
      <div className="text-lg font-bold text-white">{value}</div>
    </div>
  );
}

function PipelineOverview({ runs, onAgentClick, selectedAgent }: {
  runs: AgentRunData[];
  onAgentClick: (agentId: string) => void;
  selectedAgent: string | null;
}) {
  const runMap = useMemo(() => {
    const map: Record<string, AgentRunData> = {};
    runs.forEach(r => { map[r.agent_name] = r; });
    return map;
  }, [runs]);

  return (
    <div className="bg-gray-900/50 border border-white/5 rounded-3xl p-6 overflow-x-auto">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-2xl">🔄</span>
        <h3 className="text-lg font-bold text-white">Agent Collaboration Pipeline</h3>
        <span className="ml-auto text-xs text-gray-400">Click nodes for details</span>
      </div>
      <div className="flex items-start gap-1 sm:gap-2 lg:gap-3 px-2 py-4 min-w-max">
        {AGENT_PIPELINE.map((agent, index) => {
          const run = runMap[agent.id];
          const status = (run?.status as AgentStatus) || "waiting";
          const isActive = selectedAgent === agent.id && status === "running";
          const isCompleted = status === "completed";

          return (
            <AgentNode
              key={agent.id}
              agent={agent}
              status={status}
              isActive={isActive}
              isCompleted={isCompleted}
              index={index}
              total={AGENT_PIPELINE.length}
              onClick={() => onAgentClick(agent.id)}
            />
          );
        })}
      </div>
    </div>
  );
}

function StatusLegend() {
  return (
    <div className="flex flex-wrap items-center gap-4 p-4 bg-gray-900/50 border border-white/5 rounded-2xl">
      <span className="text-xs text-gray-400 font-semibold">Status:</span>
      {Object.entries(STATUS_CONFIG).map(([status, config]) => (
        <span key={status} className="flex items-center gap-1.5">
          <span className={`w-2 h-2 rounded-full ${config.bgColor.replace("/10", "/50").replace("bg-", "bg-")} ${status === "running" ? "animate-pulse" : ""}`} />
          <span className={`text-[10px] font-medium ${config.color}`}>{config.label}</span>
        </span>
      ))}
    </div>
  );
}

function ProgressBar({ completed, total }: { completed: number; total: number }) {
  const percentage = total > 0 ? (completed / total) * 100 : 0;
  return (
    <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
      <div
        className="h-full bg-gradient-to-r from-indigo-500 to-emerald-500 rounded-full transition-all duration-500"
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}

export function AgentVisualization({ projectId, runs }: {
  projectId: number;
  runs: AgentRunData[];
}) {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [detailData, setDetailData] = useState<Record<string, AgentDetailData>>({});

  const runMap = useMemo(() => {
    const map: Record<string, AgentRunData> = {};
    runs.forEach(r => { map[r.agent_name] = r; });
    return map;
  }, [runs]);

  const completedCount = runs.filter(r => r.status === "completed").length;
  const failedCount = runs.filter(r => r.status === "failed").length;
  const runningCount = runs.filter(r => r.status === "running").length;

  useEffect(() => {
    if (runs.length > 0) {
      const running = runs.find(r => r.status === "running");
      if (running) {
        setSelectedAgent(running.agent_name);
      } else {
        const lastDone = [...runs].reverse().find(r => r.status === "completed" || r.status === "failed");
        if (lastDone) setSelectedAgent(lastDone.agent_name);
      }
    }
  }, [runs.length]);

  const handleAgentClick = (agentId: string) => {
    setSelectedAgent(agentId);
  };

  const selectedRun = runMap[selectedAgent || ""];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white">Agent Collaboration Visualization</h2>
          <p className="text-sm text-gray-400">Project #{projectId} • {runs.length} agents in pipeline</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <ProgressBar completed={completedCount} total={AGENT_PIPELINE.length} className="w-32" />
              <span className="text-white font-medium">{completedCount}/{AGENT_PIPELINE.length} Completed</span>
            </div>
            {failedCount > 0 && (
              <span className="text-red-400 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-red-500" /> {failedCount} Failed
              </span>
            )}
            {runningCount > 0 && (
              <span className="text-yellow-400 flex items-center gap-1 animate-pulse">
                <span className="w-2 h-2 rounded-full bg-yellow-500" /> {runningCount} Running
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <PipelineOverview runs={runs} onAgentClick={handleAgentClick} selectedAgent={selectedAgent} />
          <StatusLegend />
        </div>

        <div className="lg:col-span-1">
          <AgentDetailPanel
            agent={selectedAgent ? AGENT_PIPELINE.find(a => a.id === selectedAgent) || null : null}
            runData={selectedRun || null}
            detailData={detailData[selectedAgent || ""] || null}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <AgentStatsCard title="Total Execution Time" value={
          runs.reduce((sum, r) => sum + (r.execution_time_seconds || 0), 0).toFixed(1) + "s"
        } icon="⏱️" color="indigo" />
        <AgentStatsCard title="Total Retries" value={
          runs.reduce((sum, r) => sum + r.retry_count, 0).toString()
        } icon="🔄" color="orange" />
        <AgentStatsCard title="Overall Status" value={
          failedCount > 0 ? "Failed" : completedCount === AGENT_PIPELINE.length ? "Success" : "In Progress"
        } icon={failedCount > 0 ? "❌" : completedCount === AGENT_PIPELINE.length ? "✅" : "⏳"} color={
          failedCount > 0 ? "red" : completedCount === AGENT_PIPELINE.length ? "emerald" : "yellow"
        } />
      </div>
    </div>
  );
}

function AgentStatsCard({ title, value, icon, color }: { title: string; value: string; icon: string; color: string }) {
  const colorMap: Record<string, string> = {
    indigo: "bg-indigo-500/10 border-indigo-500/20 text-indigo-400",
    orange: "bg-orange-500/10 border-orange-500/20 text-orange-400",
    emerald: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
    red: "bg-red-500/10 border-red-500/20 text-red-400",
    yellow: "bg-yellow-500/10 border-yellow-500/20 text-yellow-400",
  };
  const cls = colorMap[color] || colorMap.indigo;

  return (
    <div className={`p-4 rounded-2xl border ${cls}`}>
      <div className="flex items-center gap-3">
        <span className="text-2xl">{icon}</span>
        <div>
          <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider">{title}</p>
          <p className="text-xl font-bold text-white">{value}</p>
        </div>
      </div>
    </div>
  );
}

export default AgentVisualization;