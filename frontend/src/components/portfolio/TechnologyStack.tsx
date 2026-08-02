"use client";

import React from "react";

interface TechStackProps {
  stack: string[];
}

export const TechnologyStack: React.FC<TechStackProps> = ({ stack }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mt-6">
      <h3 className="text-lg font-bold text-white mb-4">Technology Stack & Frameworks</h3>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 text-xs">
        {stack.map((item, i) => (
          <div key={i} className="bg-slate-800/40 p-3 rounded-lg border border-slate-700/40 text-center font-bold text-white">
            {item}
          </div>
        ))}
      </div>
    </div>
  );
};
