"use client";

import React from "react";

interface Props {
  projectId: number;
}

export default function ContextTimeline({ projectId }: Props) {
  const events = [
    { time: "T+0s", title: "Project & Requirement Context", desc: "Aggregated initial project scope, BA entity models, and memory context." },
    { time: "T+2s", title: "Architecture & Database Context", desc: "Solution Architect & DB Engineer specs aggregated and validated." },
    { time: "T+5s", title: "API & Backend Context Routing", desc: "Backend Developer received Architecture, API, Security, Testing, and RAG context." },
    { time: "T+8s", title: "Security & QA Validation Context", desc: "Cross-agent validation check completed with 95% confidence score." },
    { time: "T+12s", title: "Deployment & Export Context", desc: "Generated final documentation, Docker devops deployment script, and zip archive." },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-100 shadow-2xl">
      <h3 className="text-md font-bold text-blue-400 mb-4 flex items-center gap-2">
        <span>⏱️</span> Context Creation & Evolution Timeline
      </h3>
      <div className="border-l-2 border-slate-700 ml-2 pl-4 space-y-4 text-xs">
        {events.map((ev, idx) => (
          <div key={idx} className="relative">
            <div className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-blue-500"></div>
            <div className="font-bold text-slate-200">{ev.time} — {ev.title}</div>
            <div className="text-slate-400 mt-0.5">{ev.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
