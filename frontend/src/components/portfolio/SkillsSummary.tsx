"use client";

import React from "react";

interface SkillsSummaryProps {
  skills: string[];
}

export const SkillsSummary: React.FC<SkillsSummaryProps> = ({ skills }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mt-6">
      <h3 className="text-lg font-bold text-white mb-4">Domain Skills & Technical Expertise</h3>

      <div className="flex flex-wrap gap-2">
        {skills.map((sk, i) => (
          <span key={i} className="text-xs px-3 py-1.5 rounded-lg bg-blue-500/10 text-blue-300 border border-blue-500/20 font-semibold">
            {sk}
          </span>
        ))}
      </div>
    </div>
  );
};
