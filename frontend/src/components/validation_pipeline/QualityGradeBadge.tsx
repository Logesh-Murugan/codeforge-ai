"use client";

import React from "react";

interface QualityGradeBadgeProps {
  score: number;
  grade: string;
}

export const QualityGradeBadge: React.FC<QualityGradeBadgeProps> = ({ score, grade }) => {
  const getBadgeColor = (g: string) => {
    switch (g) {
      case "A+":
      case "A":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
      case "B":
        return "bg-blue-500/10 text-blue-400 border-blue-500/30";
      case "C":
        return "bg-amber-500/10 text-amber-400 border-amber-500/30";
      default:
        return "bg-red-500/10 text-red-400 border-red-500/30";
    }
  };

  return (
    <div className="flex items-center space-x-3 bg-slate-900 border border-slate-800 p-4 rounded-xl shadow-xl">
      <div className={`w-14 h-14 rounded-full border-2 flex items-center justify-center font-extrabold text-xl ${getBadgeColor(grade)}`}>
        {grade}
      </div>
      <div>
        <span className="text-xs text-slate-400 block">Overall Quality Score</span>
        <span className="text-2xl font-bold text-white">{score.toFixed(1)} / 100</span>
      </div>
    </div>
  );
};
