"use client";

import React from "react";

export interface TimelineEvent {
  event_id: string;
  project_id: number;
  timestamp: string;
  agent_name?: string;
  stage_name?: string;
  status: string;
  duration_ms: number;
  retry_count: number;
  model_used?: string;
  provider_used?: string;
  generated_files_count: number;
  validation_score: number;
}

interface TimelineNodeProps {
  event: TimelineEvent;
  isLast?: boolean;
}

export const TimelineNode: React.FC<TimelineNodeProps> = ({ event, isLast }) => {
  const isSuccess = event.status === "COMPLETED";

  return (
    <div className="relative pl-8 pb-8 group">
      {!isLast && (
        <span className="absolute left-3 top-4 bottom-0 w-0.5 bg-slate-800 group-hover:bg-blue-500/50 transition" />
      )}
      <span
        className={`absolute left-1 top-1.5 w-4 h-4 rounded-full border-2 bg-slate-900 ${
          isSuccess ? "border-emerald-400 text-emerald-400" : "border-blue-400 text-blue-400"
        }`}
      />

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg hover:border-slate-700 transition space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono font-bold text-blue-400">{event.event_id}</span>
            <span className="text-sm font-semibold text-white">{event.stage_name || event.agent_name}</span>
          </div>
          <span className="text-[10px] px-2 py-0.5 rounded font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            {event.status}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs text-slate-400">
          <div>
            <span className="block text-[10px]">Agent</span>
            <span className="text-slate-200 font-medium">{event.agent_name || "System"}</span>
          </div>
          <div>
            <span className="block text-[10px]">Duration</span>
            <span className="text-slate-200 font-medium">{event.duration_ms}ms</span>
          </div>
          <div>
            <span className="block text-[10px]">Files Generated</span>
            <span className="text-slate-200 font-medium">{event.generated_files_count}</span>
          </div>
          <div>
            <span className="block text-[10px]">Validation Score</span>
            <span className="text-emerald-400 font-medium">{(event.validation_score * 100).toFixed(0)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
};
