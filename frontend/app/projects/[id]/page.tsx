/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars, react-hooks/exhaustive-deps, react/no-unescaped-entities */
"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getProjectStatus, downloadProject } from "@/lib/api";

interface AgentRun {
  id: number;
  agent_name: string;
  status: string;
  output_json: any | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

const AGENT_ORDER = [
  "project_manager",
  "business_analyst",
  "product_owner",
  "solution_architect",
  "backend_developer",
  "frontend_developer",
  "code_reviewer",
  "doc_writer",
];

const AGENT_META: Record<string, { label: string; icon: string; desc: string }> = {
  project_manager: {
    label: "Project Manager",
    icon: "📋",
    desc: "Creates a master plan, defines milestones, goals, and execution dependencies.",
  },
  business_analyst: {
    label: "Business Analyst",
    icon: "📊",
    desc: "Extracts data entities, core actions, and auth requirements from the plan.",
  },
  product_owner: {
    label: "Product Owner",
    icon: "👑",
    desc: "Prioritizes backlog (MoSCoW), sprint goals, and details user story acceptance criteria.",
  },
  solution_architect: {
    label: "Solution Architect",
    icon: "📐",
    desc: "Designs the PostgreSQL schema, API endpoints, and codebase directory layout.",
  },
  backend_developer: {
    label: "Backend Developer",
    icon: "💻",
    desc: "Generates SQLAlchemy models, schemas, and routes in clean FastAPI code.",
  },
  frontend_developer: {
    label: "Frontend Developer",
    icon: "🖥️",
    desc: "Generates Next.js dashboard pages, forms, and API client integration layer using React Query.",
  },
  code_reviewer: {
    label: "Code Reviewer",
    icon: "🛡️",
    desc: "Checks code for security risks (SQL injection, auth checks) and applies styling fixes.",
  },
  doc_writer: {
    label: "Doc Writer",
    icon: "📝",
    desc: "Generates installation setup instructions, and a detailed endpoint summary in a README.",
  },
};

export default function ProjectStatusPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = Number(params.id);
  
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<string>("project_manager");
  const [activeCodeFile, setActiveCodeFile] = useState<string>("");
  const [activeFixedFile, setActiveFixedFile] = useState<string>("");
  const [logs, setLogs] = useState<string[]>([]);

  const isAllDone = runs.length === 8 && runs.every((r) => r.status === "completed");
  const anyFailed = runs.some((r) => r.status === "failed");

  // Determine current active agent based on run status
  useEffect(() => {
    if (runs.length > 0) {
      const running = runs.find((r) => r.status === "running");
      if (running) {
        setSelectedAgent(running.agent_name);
      } else {
        // Find the latest completed or failed agent
        const completed = [...runs].reverse().find((r) => r.status === "completed" || r.status === "failed");
        if (completed) {
          setSelectedAgent(completed.agent_name);
        }
      }
    }
  }, [runs.length]);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await getProjectStatus(projectId);
        setRuns(data);

        // Populate logs based on runs
        const newLogs: string[] = [];
        data.forEach((run: AgentRun) => {
          const time = new Date(run.updated_at).toLocaleTimeString();
          if (run.status === "running") {
            newLogs.push(`[${time}] Agent ${AGENT_META[run.agent_name]?.label} is now running...`);
          } else if (run.status === "completed") {
            newLogs.push(`[${time}] Agent ${AGENT_META[run.agent_name]?.label} completed successfully!`);
          } else if (run.status === "failed") {
            newLogs.push(`[${time}] ❌ Agent ${AGENT_META[run.agent_name]?.label} failed: ${run.error_message}`);
          }
        });
        setLogs(newLogs);
      } catch (err) {
        console.error("Error fetching status:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);

    return () => clearInterval(interval);
  }, [projectId]);

  // Set default code files when backend dev or reviewer gets populated
  const devRun = runs.find((r) => r.agent_name === "backend_developer" && r.status === "completed");
  useEffect(() => {
    if (devRun && devRun.output_json && devRun.output_json.files && devRun.output_json.files.length > 0 && !activeCodeFile) {
      setActiveCodeFile(devRun.output_json.files[0].path);
    }
  }, [devRun, activeCodeFile]);

  const reviewerRun = runs.find((r) => r.agent_name === "code_reviewer" && r.status === "completed");
  useEffect(() => {
    if (reviewerRun && reviewerRun.output_json && reviewerRun.output_json.auto_fixed_files && reviewerRun.output_json.auto_fixed_files.length > 0 && !activeFixedFile) {
      setActiveFixedFile(reviewerRun.output_json.auto_fixed_files[0].path);
    }
  }, [reviewerRun, activeFixedFile]);

  const getAgentRun = (name: string) => {
    return runs.find((r) => r.agent_name === name);
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case "running":
        return (
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-yellow-500"></span>
          </span>
        );
      case "completed":
        return <span className="text-emerald-400 font-bold text-sm">✓</span>;
      case "failed":
        return <span className="text-red-500 font-bold text-sm">✗</span>;
      default:
        return <span className="w-2 h-2 rounded-full bg-gray-600"></span>;
    }
  };

  const getStatusTextClasses = (status?: string) => {
    switch (status) {
      case "running":
        return "text-yellow-400 font-medium";
      case "completed":
        return "text-emerald-400 font-medium";
      case "failed":
        return "text-red-400 font-medium";
      default:
        return "text-gray-500";
    }
  };

  // RENDER WORKSPACE OUTPUT PANELS BASED ON CURRENT SELECTION
  const renderAgentOutput = () => {
    const run = getAgentRun(selectedAgent);

    if (!run) {
      return (
        <div className="flex flex-col items-center justify-center h-full py-16 text-center text-gray-500">
          <div className="text-4xl mb-4">💤</div>
          <h3 className="font-bold text-white mb-1">Queueing Agent</h3>
          <p className="text-xs max-w-xs mx-auto">This agent is waiting for the previous pipeline steps to complete.</p>
        </div>
      );
    }

    if (run.status === "running") {
      return (
        <div className="flex flex-col items-center justify-center h-full py-16 text-center">
          <div className="w-12 h-12 rounded-xl border-t-2 border-indigo-500 border-r-2 border-r-transparent animate-spin mb-4" />
          <h3 className="font-bold text-white mb-1">Agent working...</h3>
          <p className="text-xs text-gray-400 max-w-xs mx-auto">
            Executing model prompts, structuring JSON parameters, and compiling response schemas.
          </p>
        </div>
      );
    }

    if (run.status === "failed") {
      return (
        <div className="glass-panel border-red-500/20 bg-red-950/10 rounded-2xl p-6 text-left">
          <div className="flex items-center space-x-2 text-red-400 mb-4">
            <span className="text-xl">⚠️</span>
            <h3 className="font-bold text-white">Agent Execution Interrupted</h3>
          </div>
          <p className="text-sm text-gray-300 mb-4">
            An error occurred while compiling this agent's workspace deliverables. The pipeline has been halted to prevent downstream code corruption.
          </p>
          <div className="bg-black/50 rounded-xl p-4 font-mono text-xs text-red-300 border border-white/5 overflow-x-auto whitespace-pre-wrap">
            {run.error_message || "Unknown execution exception."}
          </div>
        </div>
      );
    }

    const data = run.output_json;
    if (!data) return null;

    switch (selectedAgent) {
      case "project_manager":
        return (
          <div className="space-y-6">
            <div className="bg-white/5 border border-white/5 rounded-2xl p-5">
              <span className="text-[10px] text-indigo-400 font-semibold uppercase tracking-wider block mb-1">Project Summary</span>
              <p className="text-sm text-white leading-relaxed">{data.project_summary}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white/5 border border-white/5 rounded-2xl p-5 space-y-3">
                <span className="text-[10px] text-indigo-400 font-semibold uppercase tracking-wider block">Scope Boundaries</span>
                <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">{data.project_scope}</p>
              </div>
              <div className="bg-white/5 border border-white/5 rounded-2xl p-5 space-y-3">
                <span className="text-[10px] text-indigo-400 font-semibold uppercase tracking-wider block">Estimated Complexity</span>
                <div className="flex items-center space-x-2">
                  <span className={`px-3 py-1 rounded-xl text-xs font-bold uppercase border ${
                    data.estimated_complexity === "low" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                    data.estimated_complexity === "medium" ? "bg-blue-500/10 text-blue-400 border-blue-500/20" :
                    data.estimated_complexity === "high" ? "bg-amber-500/10 text-amber-400 border-amber-500/20" :
                    "bg-red-500/10 text-red-400 border-red-500/20"
                  }`}>
                    {data.estimated_complexity}
                  </span>
                </div>
              </div>
            </div>

            {data.goals?.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Project Goals</h4>
                <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {data.goals.map((goal: string, i: number) => (
                    <li key={i} className="flex items-start space-x-2 text-xs text-gray-300">
                      <span className="text-indigo-400 mt-0.5">•</span>
                      <span>{goal}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {data.milestones?.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Milestones & Phases</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {data.milestones.map((ms: any, i: number) => (
                    <div key={i} className="bg-white/5 border border-white/5 rounded-2xl p-4 space-y-2">
                      <h5 className="font-bold text-white text-xs flex items-center space-x-2">
                        <span className="bg-indigo-500/20 text-indigo-400 px-2 py-0.5 rounded text-[10px]">{i + 1}</span>
                        <span>{ms.name}</span>
                      </h5>
                      <p className="text-[11px] text-gray-400 leading-relaxed">{ms.description}</p>
                      {ms.deliverables?.length > 0 && (
                        <div className="pt-2">
                          <span className="text-[9px] text-gray-500 font-bold uppercase tracking-wider block mb-1">Deliverables</span>
                          <div className="flex flex-wrap gap-1">
                            {ms.deliverables.map((del: string, j: number) => (
                              <span key={j} className="bg-black/20 text-gray-300 px-1.5 py-0.5 rounded text-[9px] border border-white/5">
                                {del}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {data.agent_execution_plan?.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Agent Execution Steps</h4>
                <div className="overflow-x-auto border border-white/5 rounded-2xl">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="bg-white/5 border-b border-white/5 text-gray-400">
                        <th className="px-4 py-3">Agent</th>
                        <th className="px-4 py-3">Input Dependency</th>
                        <th className="px-4 py-3">Execution Role</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {data.agent_execution_plan.map((step: any, i: number) => (
                        <tr key={i} className="hover:bg-white/5 transition-colors text-[11px]">
                          <td className="px-4 py-2.5 font-bold text-indigo-300">{step.agent}</td>
                          <td className="px-4 py-2.5 font-mono text-gray-400">{step.input_from || "User Prompt / Raw Idea"}</td>
                          <td className="px-4 py-2.5 text-gray-300">{step.description}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {data.risks?.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Identified Risks</h4>
                  <ul className="space-y-1.5">
                    {data.risks.map((risk: string, i: number) => (
                      <li key={i} className="flex items-start space-x-2 text-[11px] text-gray-300 bg-red-950/10 border border-red-500/10 rounded-xl p-2.5">
                        <span className="text-red-400">⚠️</span>
                        <span>{risk}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {data.assumptions?.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Assumptions</h4>
                  <ul className="space-y-1.5">
                    {data.assumptions.map((asm: string, i: number) => (
                      <li key={i} className="flex items-start space-x-2 text-[11px] text-gray-300 bg-white/5 border border-white/5 rounded-xl p-2.5">
                        <span className="text-indigo-400">✓</span>
                        <span>{asm}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        );

      case "business_analyst":
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between bg-white/5 rounded-2xl p-4 border border-white/5">
              <div>
                <span className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider block">Security Schema</span>
                <span className="text-sm font-bold text-white">Authentication Requirements</span>
              </div>
              <span className={`px-3 py-1 rounded-xl text-xs font-semibold uppercase border ${
                data.requires_auth 
                  ? "bg-indigo-500/10 text-indigo-400 border-indigo-500/20" 
                  : "bg-white/5 text-gray-400 border-white/5"
              }`}>
                {data.requires_auth ? "Required" : "Not Required"}
              </span>
            </div>

            <div>
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Extracted Entities</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {data.entities?.map((entity: any, i: number) => (
                  <div key={i} className="bg-white/5 border border-white/5 rounded-2xl p-4">
                    <h5 className="font-bold text-indigo-300 text-sm mb-2">{entity.name}</h5>
                    <div className="flex flex-wrap gap-1.5">
                      {entity.fields?.map((field: string, j: number) => (
                        <span key={j} className="bg-black/20 text-gray-300 px-2 py-0.5 rounded text-[11px] border border-white/5">
                          {field}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {data.relationships?.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Database Relationships</h4>
                <div className="space-y-2">
                  {data.relationships.map((rel: any, i: number) => (
                    <div key={i} className="flex items-center space-x-3 bg-white/5 rounded-xl p-3 border border-white/5 text-xs text-gray-300">
                      <span className="font-bold text-white">{rel.from_ || rel.from}</span>
                      <span className="text-indigo-400">──({rel.type})──&gt;</span>
                      <span className="font-bold text-white">{rel.to}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {data.core_actions?.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Core Application Actions</h4>
                <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {data.core_actions.map((act: string, i: number) => (
                    <li key={i} className="flex items-center space-x-2 text-xs text-gray-300">
                      <span className="text-indigo-400">•</span>
                      <span>{act}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        );

      case "product_owner":
        return (
          <div className="space-y-6">
            {/* Sprint Goals */}
            {data.sprint_goals?.length > 0 && (
              <div className="bg-white/5 border border-white/5 rounded-2xl p-5">
                <span className="text-[10px] text-indigo-400 font-semibold uppercase tracking-wider block mb-2">Sprint Goals</span>
                <ul className="space-y-1.5 text-xs text-white leading-relaxed">
                  {data.sprint_goals.map((goal: string, i: number) => (
                    <li key={i} className="flex items-start space-x-2">
                      <span className="text-indigo-400 mt-0.5">•</span>
                      <span>{goal}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Backlog Items */}
            {data.backlog?.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Prioritized Product Backlog</h4>
                <div className="overflow-x-auto border border-white/5 rounded-2xl">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="bg-white/5 border-b border-white/5 text-gray-400">
                        <th className="px-4 py-3">Feature</th>
                        <th className="px-4 py-3">Priority Score</th>
                        <th className="px-4 py-3">Value</th>
                        <th className="px-4 py-3">Risk</th>
                        <th className="px-4 py-3">Dependencies</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {data.backlog.map((item: any, i: number) => {
                        const scoreColor =
                          item.priority_score >= 8 ? "text-red-400 font-bold" :
                          item.priority_score >= 5 ? "text-amber-400 font-bold" :
                          "text-emerald-400";
                        const valueColor =
                          item.business_value === "high" ? "bg-red-500/10 text-red-400 border-red-500/20" :
                          item.business_value === "medium" ? "bg-amber-500/10 text-amber-400 border-amber-500/20" :
                          "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
                        const riskColor =
                          item.risk_level === "high" ? "bg-red-500/10 text-red-400 border-red-500/20" :
                          item.risk_level === "medium" ? "bg-amber-500/10 text-amber-400 border-amber-500/20" :
                          "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
                        return (
                          <tr key={i} className="hover:bg-white/5 transition-colors">
                            <td className="px-4 py-3">
                              <div className="font-bold text-white mb-0.5">{item.feature_name}</div>
                              <div className="text-[11px] text-gray-400 leading-relaxed">{item.description}</div>
                              {item.acceptance_criteria?.length > 0 && (
                                <div className="mt-1.5 pl-2 border-l border-white/10 space-y-1">
                                  <span className="text-[9px] text-gray-500 font-bold uppercase tracking-wider block">Acceptance Criteria</span>
                                  {item.acceptance_criteria.map((ac: string, j: number) => (
                                    <div key={j} className="text-[10px] text-gray-500 flex items-center space-x-1.5">
                                      <span>◽</span>
                                      <span>{ac}</span>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </td>
                            <td className="px-4 py-3 font-mono text-center">
                              <span className={scoreColor}>{item.priority_score} / 10</span>
                            </td>
                            <td className="px-4 py-3 text-center">
                              <span className={`px-2 py-0.5 rounded text-[10px] uppercase border ${valueColor}`}>
                                {item.business_value}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-center">
                              <span className={`px-2 py-0.5 rounded text-[10px] uppercase border ${riskColor}`}>
                                {item.risk_level}
                              </span>
                            </td>
                            <td className="px-4 py-3 font-mono text-[10px] text-gray-400">
                              {item.dependencies?.length > 0 ? item.dependencies.join(", ") : "None"}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* MoSCoW Categories Overview */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-white/5 border border-white/5 rounded-2xl p-4">
                <span className="text-[10px] text-red-400 font-bold uppercase tracking-wider block mb-2">🔴 Must Have Features</span>
                <ul className="space-y-1 text-xs text-gray-300">
                  {data.must_have_features?.map((f: string, i: number) => <li key={i}>• {f}</li>)}
                </ul>
              </div>
              <div className="bg-white/5 border border-white/5 rounded-2xl p-4">
                <span className="text-[10px] text-amber-400 font-bold uppercase tracking-wider block mb-2">🟡 Should Have Features</span>
                <ul className="space-y-1 text-xs text-gray-300">
                  {data.should_have_features?.map((f: string, i: number) => <li key={i}>• {f}</li>)}
                </ul>
              </div>
              <div className="bg-white/5 border border-white/5 rounded-2xl p-4">
                <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider block mb-2">🟢 Could Have Features</span>
                <ul className="space-y-1 text-xs text-gray-300">
                  {data.could_have_features?.map((f: string, i: number) => <li key={i}>• {f}</li>)}
                </ul>
              </div>
              <div className="bg-white/5 border border-white/5 rounded-2xl p-4">
                <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block mb-2">⚪ Won't Have (Deferred)</span>
                <ul className="space-y-1 text-xs text-gray-500">
                  {data.wont_have_features?.map((f: string, i: number) => <li key={i}>• {f}</li>)}
                </ul>
              </div>
            </div>
          </div>
        );

      case "solution_architect":
        return (
          <div className="space-y-6">
            <div>
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Relational DB Schema</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {data.db_schema?.map((schema: any, i: number) => (
                  <div key={i} className="bg-white/5 border border-white/5 rounded-2xl overflow-hidden text-xs">
                    <div className="bg-white/10 px-4 py-2 font-bold text-white border-b border-white/5">
                      🗄️ {schema.table}
                    </div>
                    <div className="divide-y divide-white/5">
                      {schema.columns?.map((col: any, j: number) => (
                        <div key={j} className="px-4 py-2.5 flex justify-between items-center text-gray-300">
                          <span className="font-mono">{col.name}</span>
                          <div className="flex items-center space-x-2">
                            <span className="text-gray-500 font-mono text-[10px]">{col.type}</span>
                            {col.is_fk && (
                              <span className="bg-purple-500/10 text-purple-400 border border-purple-500/25 px-1.5 py-0.5 rounded text-[8px] font-bold uppercase">
                                FK → {col.references}
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Target Endpoints & REST API</h4>
              <div className="overflow-x-auto border border-white/5 rounded-2xl">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-white/5 border-b border-white/5 text-gray-400">
                      <th className="px-4 py-3">Method</th>
                      <th className="px-4 py-3">Path</th>
                      <th className="px-4 py-3">Description</th>
                      <th className="px-4 py-3 text-right">Auth</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {data.endpoints?.map((ep: any, i: number) => {
                      const methodColor = 
                        ep.method.toUpperCase() === "GET" ? "bg-blue-500/10 text-blue-400 border-blue-500/20" :
                        ep.method.toUpperCase() === "POST" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                        "bg-red-500/10 text-red-400 border-red-500/20";
                      return (
                        <tr key={i} className="hover:bg-white/5 transition-colors">
                          <td className="px-4 py-3">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${methodColor}`}>
                              {ep.method}
                            </span>
                          </td>
                          <td className="px-4 py-3 font-mono text-white">{ep.path}</td>
                          <td className="px-4 py-3 text-gray-400">{ep.description}</td>
                          <td className="px-4 py-3 text-right">
                            <span className={`text-[10px] ${ep.requires_auth ? "text-indigo-400 font-bold" : "text-gray-600"}`}>
                              {ep.requires_auth ? "JWT" : "None"}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {data.file_structure?.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Project Directory Layout</h4>
                <div className="bg-black/40 rounded-2xl p-4 border border-white/5 font-mono text-xs text-gray-300">
                  {data.file_structure.map((file: string, i: number) => (
                    <div key={i} className="py-1">
                      📂 {file}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );

      case "backend_developer":
        const currentFileObj = data.files?.find((f: any) => f.path === activeCodeFile);
        return (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 h-[500px]">
            {/* File Switcher Sidebar */}
            <div className="lg:col-span-1 border border-white/5 rounded-2xl bg-black/20 overflow-y-auto divide-y divide-white/5">
              <div className="px-3 py-2 bg-white/5 text-gray-400 font-semibold text-[10px] uppercase tracking-wider">
                Source Files
              </div>
              {data.files?.map((file: any, i: number) => (
                <button
                  key={i}
                  onClick={() => setActiveCodeFile(file.path)}
                  className={`w-full text-left px-4 py-2.5 text-xs transition-colors flex items-center space-x-2 ${
                    activeCodeFile === file.path
                      ? "bg-indigo-500/10 text-indigo-400 font-semibold"
                      : "text-gray-400 hover:bg-white/5 hover:text-white"
                  }`}
                >
                  <span>📄</span>
                  <span className="truncate">{file.path}</span>
                </button>
              ))}
            </div>

            {/* Code Content Screen */}
            <div className="lg:col-span-3 border border-white/5 rounded-2xl overflow-hidden flex flex-col h-full bg-[#0a0d1e]">
              <div className="px-4 py-2 bg-black/40 border-b border-white/5 text-xs text-gray-400 flex justify-between items-center font-mono">
                <span>{activeCodeFile || "select file"}</span>
                <span className="text-[10px] text-gray-600">python / sql</span>
              </div>
              <div className="flex-1 overflow-auto p-4 font-mono text-[12px] leading-relaxed text-gray-300 whitespace-pre scroll-smooth">
                {currentFileObj?.content || "# Empty file"}
              </div>
            </div>
          </div>
        );

      case "frontend_developer":
        const currentFeFileObj = data.files?.find((f: any) => f.path === activeCodeFile);
        return (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 h-[500px]">
            {/* File Switcher Sidebar */}
            <div className="lg:col-span-1 border border-white/5 rounded-2xl bg-black/20 overflow-y-auto divide-y divide-white/5">
              <div className="px-3 py-2 bg-white/5 text-gray-400 font-semibold text-[10px] uppercase tracking-wider">
                React Components
              </div>
              {data.files?.map((file: any, i: number) => (
                <button
                  key={i}
                  onClick={() => setActiveCodeFile(file.path)}
                  className={`w-full text-left px-4 py-2.5 text-xs transition-colors flex items-center space-x-2 ${
                    activeCodeFile === file.path
                      ? "bg-indigo-500/10 text-indigo-400 font-semibold"
                      : "text-gray-400 hover:bg-white/5 hover:text-white"
                  }`}
                >
                  <span>📄</span>
                  <span className="truncate">{file.path.replace("frontend/", "")}</span>
                </button>
              ))}
            </div>

            {/* Code Content Screen */}
            <div className="lg:col-span-3 border border-white/5 rounded-2xl overflow-hidden flex flex-col h-full bg-[#0a0d1e]">
              <div className="px-4 py-2 bg-black/40 border-b border-white/5 text-xs text-gray-400 flex justify-between items-center font-mono">
                <span>{activeCodeFile || "select file"}</span>
                <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-wider">next.js / react</span>
              </div>
              <div className="flex-1 overflow-auto p-4 font-mono text-[12px] leading-relaxed text-gray-300 whitespace-pre scroll-smooth">
                {currentFeFileObj?.content || "# Empty file"}
              </div>
            </div>
          </div>
        );

      case "code_reviewer":
        const autoFixedFileObj = data.auto_fixed_files?.find((f: any) => f.path === activeFixedFile);
        return (
          <div className="space-y-6">
            {/* Issues Log */}
            <div>
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Reviewed Issues Log</h4>
              {data.issues?.length === 0 ? (
                <div className="bg-emerald-500/5 border border-emerald-500/20 text-emerald-400 rounded-2xl p-4 text-xs font-semibold">
                  🎉 Code Review complete. Zero critical issues or formatting anomalies detected!
                </div>
              ) : (
                <div className="space-y-3">
                  {data.issues?.map((issue: any, i: number) => {
                    const sevColor = 
                      issue.severity === "critical" ? "bg-red-500/10 border-red-500/20 text-red-400" :
                      issue.severity === "warning" ? "bg-amber-500/10 border-amber-500/20 text-amber-400" :
                      "bg-white/5 border-white/10 text-gray-400";
                    return (
                      <div key={i} className={`border rounded-2xl p-4 flex flex-col sm:flex-row justify-between sm:items-center gap-2 ${sevColor}`}>
                        <div>
                          <div className="flex items-center space-x-2 mb-1">
                            <span className="font-bold text-xs capitalize uppercase tracking-wider">{issue.severity}</span>
                            <span className="text-[11px] text-white font-mono">{issue.file}{issue.line ? `:${issue.line}` : ""}</span>
                          </div>
                          <p className="text-xs text-gray-300">{issue.description}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Auto Fixed Files */}
            {data.auto_fixed_files?.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Auto-Fixed Code Files</h4>
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 h-[400px]">
                  {/* File List */}
                  <div className="lg:col-span-1 border border-white/5 rounded-2xl bg-black/20 overflow-y-auto divide-y divide-white/5">
                    <div className="px-3 py-2 bg-white/5 text-gray-400 font-semibold text-[10px] uppercase tracking-wider">
                      Fixed Files
                    </div>
                    {data.auto_fixed_files.map((file: any, i: number) => (
                      <button
                        key={i}
                        onClick={() => setActiveFixedFile(file.path)}
                        className={`w-full text-left px-4 py-2.5 text-xs transition-colors flex items-center space-x-2 ${
                          activeFixedFile === file.path
                            ? "bg-purple-500/10 text-purple-400 font-semibold"
                            : "text-gray-400 hover:bg-white/5 hover:text-white"
                        }`}
                      >
                        <span>📄</span>
                        <span className="truncate">{file.path}</span>
                      </button>
                    ))}
                  </div>

                  {/* Code viewer */}
                  <div className="lg:col-span-3 border border-white/5 rounded-2xl overflow-hidden flex flex-col h-full bg-[#0a0d1e]">
                    <div className="px-4 py-2 bg-black/40 border-b border-white/5 text-xs text-gray-400 flex justify-between items-center font-mono">
                      <span>{activeFixedFile || "select file"}</span>
                      <span className="text-[10px] text-purple-400 font-bold uppercase tracking-wider">fixed</span>
                    </div>
                    <div className="flex-1 overflow-auto p-4 font-mono text-[12px] leading-relaxed text-gray-300 whitespace-pre scroll-smooth">
                      {autoFixedFileObj?.content || "# Empty file"}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        );

      case "doc_writer":
        return (
          <div className="space-y-4">
            <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Generated Documentation (README.md)</h4>
            <div className="border border-white/5 rounded-2xl bg-black/30 p-6 overflow-y-auto h-[450px]">
              <pre className="font-mono text-xs text-gray-300 whitespace-pre-wrap leading-relaxed">
                {data.documentation || "No documentation generated."}
              </pre>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen gradient-bg flex flex-col justify-between">
      {/* Header */}
      <header className="w-full border-b border-white/5 bg-black/20 backdrop-blur-md sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => router.push("/projects")}
              className="text-gray-400 hover:text-white transition-colors text-sm font-semibold"
            >
              ← Back to Projects
            </button>
            <div className="h-4 w-[1px] bg-white/10" />
            <div className="flex items-center space-x-2">
              <span className="font-bold text-white">Project ID:</span>
              <span className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/25 px-2 py-0.5 rounded font-mono text-xs font-bold">
                {projectId}
              </span>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs text-gray-400">Live Orchestrator Active</span>
          </div>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 z-10 grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        {/* Agent Stepper Panel (Left Side) */}
        <div className="lg:col-span-1 space-y-6">
          <div className="glass-panel rounded-3xl p-6 border-white/5 shadow-xl relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-indigo-500/30 to-transparent" />
            <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-6">Orchestration Stepper</h2>
            
            <div className="relative border-l border-white/10 pl-6 ml-3 space-y-6">
              {AGENT_ORDER.map((agentName) => {
                const run = getAgentRun(agentName);
                const isSelected = selectedAgent === agentName;
                const meta = AGENT_META[agentName];

                return (
                  <div
                    key={agentName}
                    onClick={() => {
                      if (run) {
                        setSelectedAgent(agentName);
                        if (agentName === "backend_developer") {
                          if (run.output_json?.files?.length > 0) {
                            const beFile = run.output_json.files.find((f: any) => !f.path.startsWith("frontend/")) || run.output_json.files[0];
                            setActiveCodeFile(beFile.path);
                          }
                        } else if (agentName === "frontend_developer") {
                          if (run.output_json?.files?.length > 0) {
                            const feFile = run.output_json.files.find((f: any) => f.path.endsWith("package.json")) || run.output_json.files[0];
                            setActiveCodeFile(feFile.path);
                          }
                        }
                      }
                    }}
                    className={`relative cursor-pointer group ${
                      run ? "pointer-events-auto" : "pointer-events-none opacity-40"
                    }`}
                  >
                    {/* Circle Indicator on vertical line */}
                    <div className={`absolute left-[-31px] top-[2px] w-4 h-4 rounded-full border-2 bg-black flex items-center justify-center transition-all ${
                      run?.status === "running" ? "border-yellow-400 scale-110" :
                      run?.status === "completed" ? "border-emerald-400" :
                      run?.status === "failed" ? "border-red-500" :
                      "border-gray-700"
                    }`}>
                      {getStatusIcon(run?.status)}
                    </div>

                    {/* Text Details */}
                    <div>
                      <h3 className={`text-sm font-bold transition-colors flex items-center space-x-2 ${
                        isSelected 
                          ? "text-indigo-400" 
                          : "text-white group-hover:text-gray-300"
                      }`}>
                        <span>{meta?.icon}</span>
                        <span>{meta?.label}</span>
                      </h3>
                      <p className="text-[10px] text-gray-500 mt-0.5 uppercase tracking-wide">
                        Status: <span className={getStatusTextClasses(run?.status)}>{run?.status || "pending"}</span>
                      </p>
                      <p className="text-[10px] text-gray-400 mt-1 leading-snug">
                        {meta?.desc}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Terminal Console log */}
          <div className="glass-panel rounded-3xl p-6 border-white/5 shadow-xl relative overflow-hidden bg-black/40">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Terminal Output</h3>
            <div className="h-44 overflow-y-auto font-mono text-[10px] text-gray-400 space-y-2 select-text">
              {logs.length === 0 ? (
                <div className="text-gray-600 italic">No console logs output yet. Starting pipeline...</div>
              ) : (
                logs.map((log, i) => (
                  <div key={i} className="leading-relaxed whitespace-pre-wrap">
                    {log}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Workspace Display Area (Right Side) */}
        <div className="lg:col-span-3">
          <div className="glass-panel rounded-3xl p-8 border-white/5 shadow-xl h-full flex flex-col justify-between relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-purple-500/30 to-transparent" />
            
            {/* Header info for currently selected agent */}
            <div className="border-b border-white/5 pb-4 mb-6 flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                  <span>{AGENT_META[selectedAgent]?.icon}</span>
                  <span>{AGENT_META[selectedAgent]?.label} Outputs</span>
                </h2>
                <p className="text-xs text-gray-400 mt-1">Review the direct deliverables produced by this compiler node</p>
              </div>
            </div>

            {/* Dynamic Content */}
            <div className="flex-1">
              {renderAgentOutput()}
            </div>

            {/* Bottom download zip area */}
            <div className="mt-8 pt-6 border-t border-white/5 flex flex-col sm:flex-row justify-between items-center gap-4">
              <div>
                <h4 className="text-xs font-bold text-white">Ready for local integration?</h4>
                <p className="text-[10px] text-gray-400 mt-0.5">Exporter will compile all source files into a standard project ZIP.</p>
              </div>
              <button
                onClick={() => downloadProject(projectId)}
                disabled={!isAllDone || anyFailed}
                className={`px-8 py-3.5 rounded-xl font-bold text-sm text-white shadow-xl tracking-wide transition-all ${
                  isAllDone
                    ? "bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 shadow-emerald-500/20 hover:scale-[1.02] active:scale-[0.98]"
                    : "bg-white/5 border border-white/10 text-gray-500 cursor-not-allowed"
                }`}
              >
                {isAllDone 
                  ? "📦 Download Generated ZIP" 
                  : anyFailed 
                    ? "❌ Pipeline Terminated" 
                    : "⏳ Waiting for Compiler Completion..."}
              </button>
            </div>

          </div>
        </div>

      </main>

      {/* Footer */}
      <footer className="w-full border-t border-white/5 bg-black/20 backdrop-blur-md py-6 z-10 mt-8">
        <div className="max-w-7xl mx-auto px-6 text-center text-xs text-gray-500">
          © {new Date().getFullYear()} CodeForge AI. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
