"use client";

import React from "react";

interface TimelineItem {
  id: number;
  title: string;
  status: string;
  duration_ms: number;
  timestamp: string;
}

interface TimelineViewProps {
  timeline: TimelineItem[];
}

export const TimelineView: React.FC<TimelineViewProps> = ({ timeline }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mt-6">
      <h3 className="text-lg font-bold text-white mb-4">Execution Timeline</h3>

      <div className="space-y-3">
        {timeline.map((item) => (
          <div key={item.id} className="flex items-center space-x-4 bg-slate-800/40 p-3 rounded-lg border border-slate-700/40">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shrink-0" />
            <div className="flex-1">
              <span className="text-sm font-semibold text-white">{item.title}</span>
              <span className="text-xs text-slate-400 ml-2">({item.duration_ms}ms)</span>
            </div>
            <span className="text-xs font-mono text-slate-400">{item.timestamp}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
