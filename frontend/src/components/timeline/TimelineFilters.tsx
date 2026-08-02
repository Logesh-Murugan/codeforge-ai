"use client";

import React from "react";

interface TimelineFiltersProps {
  searchKeyword: string;
  setSearchKeyword: (val: string) => void;
  filterStatus: string;
  setFilterStatus: (val: string) => void;
}

export const TimelineFilters: React.FC<TimelineFiltersProps> = ({
  searchKeyword,
  setSearchKeyword,
  filterStatus,
  setFilterStatus,
}) => {
  return (
    <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-xl">
      <input
        type="text"
        placeholder="Search timeline by agent, stage, or keyword..."
        value={searchKeyword}
        onChange={(e) => setSearchKeyword(e.target.value)}
        className="bg-slate-800 border border-slate-700 text-xs text-white px-3 py-2 rounded-lg focus:outline-none focus:border-blue-500 flex-1 min-w-[200px]"
      />

      <div className="flex items-center space-x-2">
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="bg-slate-800 border border-slate-700 text-xs text-white px-3 py-2 rounded-lg focus:outline-none"
        >
          <option value="ALL">All Statuses</option>
          <option value="COMPLETED">Completed</option>
          <option value="FAILED">Failed</option>
        </select>
      </div>
    </div>
  );
};
