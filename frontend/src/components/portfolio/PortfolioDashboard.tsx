"use client";

import React, { useEffect, useState } from "react";
import { PortfolioOverview } from "./PortfolioOverview";
import { PortfolioMetrics } from "./PortfolioMetrics";
import { ArchitectureViewer } from "./ArchitectureViewer";
import { WorkflowViewer } from "./WorkflowViewer";
import { SkillsSummary } from "./SkillsSummary";
import { EngineeringTimeline } from "./EngineeringTimeline";
import { DownloadCenter } from "./DownloadCenter";
import { TechnologyStack } from "./TechnologyStack";
import { ProjectStatistics } from "./ProjectStatistics";

export const PortfolioDashboard: React.FC = () => {
  const [portfolio, setPortfolio] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchPortfolio = async () => {
    try {
      const res = await fetch("http://localhost:8000/portfolio/1");
      if (res.ok) {
        setPortfolio(await res.json());
      }
    } catch (e) {
      console.error("Portfolio fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolio();
  }, []);

  if (loading || !portfolio) {
    return (
      <div className="p-8 text-center text-slate-400">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mb-2" />
        <p>Generating Automated Engineering Portfolio Package...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-white tracking-tight">{portfolio.project_name}</h1>
          <p className="text-sm text-slate-400">Automated Software Engineering Portfolio Package</p>
        </div>
        <span className="px-3 py-1 text-xs font-bold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase">
          {portfolio.metrics.quality_grade} Grade ({portfolio.metrics.validation_score.toFixed(1)}/100)
        </span>
      </div>

      <PortfolioMetrics
        linesOfCode={portfolio.metrics.lines_of_code}
        filesCount={portfolio.metrics.number_of_files}
        apisCount={portfolio.metrics.number_of_apis}
        modelsCount={portfolio.metrics.number_of_models}
        validationScore={portfolio.metrics.validation_score}
        testCoverage={portfolio.metrics.test_coverage_pct}
      />

      <PortfolioOverview
        summary={portfolio.executive_summary}
        vision={portfolio.project_vision}
        problem={portfolio.problem_statement}
        objectives={portfolio.objectives}
      />

      <TechnologyStack stack={portfolio.technology_stack} />
      <WorkflowViewer workflows={portfolio.agent_workflows} />
      <ArchitectureViewer architecture={portfolio.architecture} diagrams={portfolio.diagrams} />
      <ProjectStatistics metrics={portfolio.metrics} />
      <EngineeringTimeline />
      <SkillsSummary skills={["FastAPI", "React", "Next.js", "SQLAlchemy", "Pydantic", "Docker", "ChromaDB", "Mermaid", "OWASP Security"]} />
      <DownloadCenter downloads={portfolio.downloads} />
    </div>
  );
};
