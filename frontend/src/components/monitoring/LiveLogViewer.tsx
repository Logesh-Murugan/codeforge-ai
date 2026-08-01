"use client";

import React, { useState } from "react";

interface LogEntry {
  id: number;
  level: string;
  source: string;
  message: string;
  timestamp: string;
}

interface LiveLogViewerProps {
  logs: LogEntry[];
}

export const LiveLogViewer: React.FC<LiveLogViewerProps> = ({ logs: initialLogs }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterSource, setFilterSource] = useState("all");
  const [isPaused, setIsPaused] = useState(false);
  const [logs, setLogs] = useState(initialLogs);

  const filtered = logs.filter((log) => {
    const matchesSearch = log.message.toLowerCase().includes(searchTerm.toLowerCase()) || log.source.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSource = filterSource === "all" || log.source.toLowerCase() === filterSource.toLowerCase();
    return matchesSearch && matchesSource;
  });

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mt-6">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
        <h3 className="text-lg font-bold text-white">Live System & Agent Logs</h3>

        <div className="flex items-center space-x-2">
          <input
            type="text"
            placeholder="Search logs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-xs text-white px-3 py-1.5 rounded focus:outline-none focus:border-blue-500"
          />

          <select
            value={filterSource}
            onChange={(e) => setFilterSource(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-xs text-white px-3 py-1.5 rounded focus:outline-none focus:border-blue-500"
          >
            <option value="all">All Sources</option>
            <option value="system">System</option>
            <option value="validationengine">Validation</option>
            <option value="backenddeveloper">Backend</option>
          </select>

          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`text-xs px-3 py-1.5 rounded font-semibold transition ${
              isPaused ? "bg-amber-500/20 text-amber-300" : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}
          >
            {isPaused ? "Paused" : "Pause"}
          </button>

          <button
            onClick={() => setLogs([])}
            className="text-xs bg-red-500/20 text-red-300 px-3 py-1.5 rounded font-semibold hover:bg-red-500/30"
          >
            Clear
          </button>
        </div>
      </div>

      <div className="bg-slate-950 font-mono text-xs p-4 rounded-lg border border-slate-800 max-h-72 overflow-y-auto space-y-1">
        {filtered.length === 0 ? (
          <div className="text-slate-500 italic">No logs found matching filter criteria.</div>
        ) : (
          filtered.map((log) => (
            <div key={log.id} className="flex space-x-2">
              <span className="text-slate-500">{log.timestamp}</span>
              <span className="text-blue-400 font-bold">[{log.source}]</span>
              <span className="text-slate-200">{log.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
