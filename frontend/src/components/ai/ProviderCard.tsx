"use client";

import React from "react";

interface Props {
  providerName: string;
  mode: string;
  healthStatus: string;
  supportedModels: string[];
  supportedEmbeddings: string[];
}

export default function ProviderCard({
  providerName,
  mode,
  healthStatus,
  supportedModels,
  supportedEmbeddings,
}: Props) {
  const isConnected = healthStatus === "Connected";

  return (
    <div className="bg-slate-800/90 border border-slate-700 rounded-xl p-5 text-slate-100 shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-700 pb-3 mb-4">
        <div>
          <h3 className="text-lg font-bold text-indigo-400 capitalize">{providerName} Provider</h3>
          <span className="text-xs text-slate-400 uppercase tracking-wider">Mode: {mode}</span>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-xs font-bold ${
            isConnected
              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
              : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
          }`}
        >
          {healthStatus}
        </span>
      </div>

      <div className="space-y-3 text-xs">
        <div>
          <span className="text-slate-400 font-semibold">Supported Models ({supportedModels.length}):</span>
          <div className="flex flex-wrap gap-1.5 mt-1.5">
            {supportedModels.map((m) => (
              <span key={m} className="px-2 py-0.5 bg-slate-900 border border-slate-700 text-slate-300 rounded">
                {m}
              </span>
            ))}
          </div>
        </div>

        <div>
          <span className="text-slate-400 font-semibold">Supported Embeddings ({supportedEmbeddings.length}):</span>
          <div className="flex flex-wrap gap-1.5 mt-1.5">
            {supportedEmbeddings.map((e) => (
              <span key={e} className="px-2 py-0.5 bg-slate-900 border border-slate-700 text-teal-300 rounded font-mono">
                {e}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
