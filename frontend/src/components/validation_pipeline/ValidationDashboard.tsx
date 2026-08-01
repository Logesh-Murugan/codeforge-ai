"use client";

import React, { useEffect, useState } from "react";
import { QualityGradeBadge } from "./QualityGradeBadge";
import { PipelineProgressCard } from "./PipelineProgressCard";
import { IssuesList } from "./IssuesList";
import { ReportsViewer } from "./ReportsViewer";
import { ValidationHistory } from "./ValidationHistory";

export const ValidationDashboard: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [running, setRunning] = useState<boolean>(false);

  const fetchLatest = async () => {
    try {
      const res = await fetch("http://localhost:8000/validation/latest?project_id=1");
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
    } catch (e) {
      console.error("Validation dashboard fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleRunValidation = async () => {
    setRunning(true);
    try {
      const res = await fetch("http://localhost:8000/validation/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_id: 1 }),
      });
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
    } catch (e) {
      console.error("Run validation error:", e);
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    fetchLatest();
  }, []);

  if (loading || !data) {
    return (
      <div className="p-8 text-center text-slate-400">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mb-2" />
        <p>Loading Automated Validation Pipeline Dashboard...</p>
      </div>
    );
  }

  const reportsMock = {
    "validation_summary.md": `# Validation Summary\n\nProject ID: ${data.project_id}\nStatus: ${data.status}\nOverall Score: ${data.overall_score.toFixed(1)}/100 (${data.quality_grade})`,
    "security_report.md": "# Security Report\n\n0 Critical / High security vulnerabilities detected.",
    "architecture_report.md": "# Architecture Report\n\nController-Service-Repository pattern verified.",
    "performance_report.md": "# Performance Report\n\nExecution Time: " + data.total_execution_time_ms.toFixed(1) + "ms",
    "quality_score.md": "# Quality Scorecard\n\nGrade: " + data.quality_grade,
    "validation.json": JSON.stringify(data, null, 2),
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">Validation Pipeline Quality Gate</h1>
          <p className="text-sm text-slate-400">Automated 12-Stage Inspection & Export Readiness Verification</p>
        </div>

        <button
          onClick={handleRunValidation}
          disabled={running}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold text-xs px-4 py-2 rounded-lg shadow-lg transition"
        >
          {running ? "Executing 12 Stages..." : "Run Validation Pipeline"}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2">
          <PipelineProgressCard stages={data.stage_results} status={data.status} />
        </div>
        <div>
          <QualityGradeBadge score={data.overall_score} grade={data.quality_grade} />
        </div>
      </div>

      <IssuesList issues={data.all_issues} />
      <ReportsViewer reports={reportsMock} />
      <ValidationHistory
        history={[
          {
            run_id: 1,
            status: data.status,
            score: data.overall_score,
            quality_grade: data.quality_grade,
            duration_ms: data.total_execution_time_ms,
            executed_at: "2026-08-01 23:20:00",
          },
        ]}
      />
    </div>
  );
};
