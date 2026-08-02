"use client";

import React from "react";

interface TimelineProgressBarProps {
  progressPct: number;
  currentStage: string;
}

export const TimelineProgressBar: React.FC<TimelineProgressBarProps> = ({ progressPct, currentStage }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
      <div className="flex justify-between items-center text-xs mb-2">
        <span className="text-slate-400">Current Stage: <strong className="text-white">{currentStage}</strong></span>
        <span className="text-blue-400 font-bold">{progressPct.toFixed(0)}%</span>
      </div>
      <div className="w-full bg-slate-800 h-3 rounded-full overflow-hidden">
        <div
          className="bg-gradient-to-r from-blue-500 via-indigo-500 to-emerald-500 h-full transition-all duration-500"
          style={{ width: `${progressPct}%` }}
        />
      </div>
    </div>
  );
};
