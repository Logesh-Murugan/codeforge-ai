"use client";

import React from "react";

interface Props {
  currentEmbedding: string;
  availableEmbeddings: string[];
  onChange: (embedding: string) => void;
}

export default function EmbeddingSelector({ currentEmbedding, availableEmbeddings, onChange }: Props) {
  return (
    <div className="bg-slate-800/80 border border-slate-700 rounded-lg p-4">
      <label className="block text-xs font-bold text-slate-300 uppercase mb-2">
        Active Embedding Model Selector
      </label>
      <select
        value={currentEmbedding}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-slate-900 border border-slate-700 text-teal-300 text-sm rounded-md p-2.5 focus:outline-none focus:border-teal-500 font-mono"
      >
        {availableEmbeddings.map((e) => (
          <option key={e} value={e}>
            {e}
          </option>
        ))}
      </select>
    </div>
  );
}
