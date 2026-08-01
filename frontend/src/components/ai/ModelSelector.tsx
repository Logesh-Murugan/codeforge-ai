"use client";

import React from "react";

interface Props {
  currentModel: string;
  availableModels: string[];
  onChange: (model: string) => void;
}

export default function ModelSelector({ currentModel, availableModels, onChange }: Props) {
  return (
    <div className="bg-slate-800/80 border border-slate-700 rounded-lg p-4">
      <label className="block text-xs font-bold text-slate-300 uppercase mb-2">
        Active LLM Model Selector
      </label>
      <select
        value={currentModel}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-slate-900 border border-slate-700 text-indigo-300 text-sm rounded-md p-2.5 focus:outline-none focus:border-indigo-500 font-mono"
      >
        {availableModels.map((m) => (
          <option key={m} value={m}>
            {m}
          </option>
        ))}
      </select>
    </div>
  );
}
