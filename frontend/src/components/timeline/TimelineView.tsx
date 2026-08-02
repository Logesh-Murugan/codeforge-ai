"use client";

import React, { useState } from "react";
import { TimelineEvent, TimelineNode } from "./TimelineNode";

interface TimelineViewProps {
  events: TimelineEvent[];
}

export const TimelineView: React.FC<TimelineViewProps> = ({ events }) => {
  const [viewMode, setViewMode] = useState<"vertical" | "swimlane">("vertical");

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mt-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-white">Chronological Execution Timeline</h3>
        <div className="flex space-x-1 bg-slate-800 p-1 rounded-lg">
          <button
            onClick={() => setViewMode("vertical")}
            className={`text-xs px-3 py-1 rounded font-semibold transition ${
              viewMode === "vertical" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            Vertical
          </button>
          <button
            onClick={() => setViewMode("swimlane")}
            className={`text-xs px-3 py-1 rounded font-semibold transition ${
              viewMode === "swimlane" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            Swimlane
          </button>
        </div>
      </div>

      {viewMode === "vertical" ? (
        <div className="mt-4">
          {events.map((evt, idx) => (
            <TimelineNode key={evt.event_id} event={evt} isLast={idx === events.length - 1} />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {events.map((evt) => (
            <div key={evt.event_id} className="flex items-center space-x-4 bg-slate-800/40 p-3 rounded-lg border border-slate-700/40 text-xs">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shrink-0" />
              <span className="w-24 font-bold text-blue-400 font-mono">{evt.event_id}</span>
              <span className="w-32 font-semibold text-white truncate">{evt.agent_name || "System"}</span>
              <span className="flex-1 text-slate-300">{evt.stage_name}</span>
              <span className="text-slate-400">{evt.duration_ms}ms</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
