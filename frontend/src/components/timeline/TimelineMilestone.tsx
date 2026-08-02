"use client";

import React from "react";

export interface Milestone {
  project_id: number;
  milestone_name: string;
  status: string;
  achieved_at: string;
}

interface TimelineMilestoneProps {
  milestones: Milestone[];
}

export const TimelineMilestone: React.FC<TimelineMilestoneProps> = ({ milestones }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
      <h3 className="text-lg font-bold text-white mb-4">Milestone Progress ({milestones.length})</h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {milestones.map((m, i) => (
          <div key={i} className="flex items-center space-x-3 bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shrink-0" />
            <div className="flex-1 truncate">
              <span className="text-xs font-semibold text-white block truncate">{m.milestone_name}</span>
              <span className="text-[10px] text-emerald-400 font-bold uppercase">{m.status}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
