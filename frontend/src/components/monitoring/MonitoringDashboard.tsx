"use client";

import React, { useEffect, useState } from "react";
import { WorkflowProgressCard } from "./WorkflowProgressCard";
import { AgentPipelineView } from "./AgentPipelineView";
import { TimelineView } from "./TimelineView";
import { LiveLogViewer } from "./LiveLogViewer";
import { PerformanceDashboard } from "./PerformanceDashboard";
import { useMonitoringWebSocket } from "../../hooks/useMonitoringWebSocket";

export const MonitoringDashboard: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const { isConnected } = useMonitoringWebSocket(1);

  const fetchDashboard = async () => {
    try {
      const res = await fetch("http://localhost:8000/monitoring/dashboard?project_id=1");
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
    } catch (e) {
      console.error("Dashboard fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading || !data) {
    return (
      <div className="p-8 text-center text-slate-400">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mb-2" />
        <p>Loading Monitoring Observability Suite...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Real-Time Observability & Monitoring</h1>
          <p className="text-sm text-slate-400">Live 13-Agent LangGraph Pipeline Telemetry & Performance Dashboard</p>
        </div>

        <div className="flex items-center space-x-2">
          <span className={`w-3 h-3 rounded-full ${isConnected ? "bg-emerald-500 animate-pulse" : "bg-amber-500"}`} />
          <span className="text-xs font-semibold text-slate-300">
            {isConnected ? "Live WebSocket Connected" : "Polling REST Endpoint"}
          </span>
        </div>
      </div>

      <WorkflowProgressCard status={data.status} />
      <AgentPipelineView agents={data.status.agents} />
      <PerformanceDashboard metrics={data.metrics} />
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TimelineView timeline={data.timeline} />
        <LiveLogViewer logs={data.logs} />
      </div>
    </div>
  );
};
