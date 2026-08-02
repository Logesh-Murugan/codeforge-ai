"use client";

import React from "react";

interface ValidationScoreCardProps {
  score: number;
  grade: string;
}

export const ValidationScoreCard: React.FC<ValidationScoreCardProps> = ({ score, grade }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl flex items-center space-x-4">
      <div className="w-16 h-16 rounded-full border-2 border-emerald-500/40 bg-emerald-500/10 flex items-center justify-center font-extrabold text-2xl text-emerald-400">
        {grade}
      </div>
      <div>
        <span className="text-xs text-slate-400 block">Overall Quality Score</span>
        <span className="text-3xl font-extrabold text-white">{score.toFixed(1)} / 100</span>
      </div>
    </div>
  );
};
