"use client";

import React, { useEffect, useState } from "react";
import { TimelineView } from "./TimelineView";
import { TimelineMilestone } from "./TimelineMilestone";
import { TimelineStatistics } from "./TimelineStatistics";
import { TimelineFilters } from "./TimelineFilters";
import { TimelineAnalytics } from "./TimelineAnalytics";
import { TimelineProgressBar } from "./TimelineProgressBar";

export const TimelineDashboard: React.FC = () => {
  const [events, setEvents] = useState<any[]>([]);
  const [milestones, setMilestones] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchKeyword, setSearchKeyword] = useState<string>("");
  const [filterStatus, setFilterStatus] = useState<string>("ALL");

  const fetchTimelineData = async () => {
    try {
      const [resEvts, resMs, resStats, resAn] = await Promise.all([
        fetch("http://localhost:8000/timeline/1"),
        fetch("http://localhost:8000/timeline/milestones/1"),
        fetch("http://localhost:8000/timeline/statistics/1"),
        fetch("http://localhost:8000/timeline/analytics/1"),
      ]);

      if (resEvts.ok) setEvents(await resEvts.json());
      if (resMs.ok) setMilestones(await resMs.json());
      if (resStats.ok) setStats(await resStats.json());
      if (resAn.ok) setAnalytics(await resAn.json());
    } catch (e) {
      console.error("Timeline data fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTimelineData();
  }, []);

  if (loading || !stats || !analytics) {
    return (
      <div className="p-8 text-center text-slate-400">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mb-2" />
        <p>Loading Project Timeline & Analytics Engine...</p>
      </div>
    );
  }

  const filteredEvents = events.filter((evt) => {
    const matchSearch =
      !searchKeyword ||
      evt.stage_name?.toLowerCase().includes(searchKeyword.toLowerCase()) ||
      evt.agent_name?.toLowerCase().includes(searchKeyword.toLowerCase());
    const matchStatus = filterStatus === "ALL" || evt.status === filterStatus;
    return matchSearch && matchStatus;
  });

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-white tracking-tight">Project Lifecycle Timeline</h1>
        <p className="text-sm text-slate-400">Central Event History, Milestone Detection & Performance Analytics Engine</p>
      </div>

      <TimelineProgressBar progressPct={stats.overall_progress_pct} currentStage={stats.current_stage} />
      <TimelineFilters
        searchKeyword={searchKeyword}
        setSearchKeyword={setSearchKeyword}
        filterStatus={filterStatus}
        setFilterStatus={setFilterStatus}
      />
      <TimelineStatistics stats={stats} />
      <TimelineMilestone milestones={milestones} />
      <TimelineView events={filteredEvents} />
      <TimelineAnalytics analytics={analytics} />
    </div>
  );
};
