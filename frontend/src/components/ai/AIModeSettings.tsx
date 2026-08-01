"use client";

import React, { useState, useEffect } from "react";
import ProviderCard from "./ProviderCard";
import ModelSelector from "./ModelSelector";
import EmbeddingSelector from "./EmbeddingSelector";

export default function AIModeSettings() {
  const [config, setConfig] = useState({
    mode: "cloud",
    active_provider: "groq",
    active_model: "llama-3.1-8b",
    active_embedding: "all-MiniLM-L6-v2",
    health_status: "Connected",
  });

  const localModels = ["qwen2.5-coder", "deepseek-r1", "llama3.1", "mistral", "phi3", "gemma"];
  const localEmbeddings = ["nomic-embed-text", "bge-small", "all-minilm"];

  const cloudModels = ["llama-3.1-8b", "llama-3.3-70b", "deepseek-r1", "mixtral", "gemma"];
  const cloudEmbeddings = ["all-MiniLM-L6-v2", "bge-small-en", "gte-small"];

  useEffect(() => {
    fetch("/api/ai-mode/current")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setConfig(data);
      })
      .catch(() => {});
  }, []);

  const handleSwitchMode = async (targetMode: string) => {
    try {
      const res = await fetch("/api/ai-mode/switch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: targetMode }),
      });
      if (res.ok) {
        const data = await res.json();
        setConfig(data);
      }
    } catch (err) {
      console.error("Failed to switch mode", err);
    }
  };

  const currentModels = config.mode === "local" ? localModels : cloudModels;
  const currentEmbeddings = config.mode === "local" ? localEmbeddings : cloudEmbeddings;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-100 shadow-2xl max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-indigo-400 flex items-center gap-2">
            <span>⚡</span> AI Mode Manager Settings
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Configure platform-wide AI Provider Gateway (LOCAL vs CLOUD mode).
          </p>
        </div>
        <div className="flex bg-slate-800 p-1 rounded-lg border border-slate-700">
          <button
            onClick={() => handleSwitchMode("local")}
            className={`px-4 py-1.5 rounded-md text-xs font-bold transition-all ${
              config.mode === "local"
                ? "bg-indigo-600 text-white shadow"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            💻 LOCAL (Ollama)
          </button>
          <button
            onClick={() => handleSwitchMode("cloud")}
            className={`px-4 py-1.5 rounded-md text-xs font-bold transition-all ${
              config.mode === "cloud"
                ? "bg-indigo-600 text-white shadow"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            ☁️ CLOUD (Groq)
          </button>
        </div>
      </div>

      <ProviderCard
        providerName={config.active_provider}
        mode={config.mode}
        healthStatus={config.health_status}
        supportedModels={currentModels}
        supportedEmbeddings={currentEmbeddings}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ModelSelector
          currentModel={config.active_model}
          availableModels={currentModels}
          onChange={(m) => setConfig({ ...config, active_model: m })}
        />
        <EmbeddingSelector
          currentEmbedding={config.active_embedding}
          availableEmbeddings={currentEmbeddings}
          onChange={(e) => setConfig({ ...config, active_embedding: e })}
        />
      </div>

      <div className="bg-slate-800/40 p-4 rounded-lg border border-slate-700 text-xs flex justify-between items-center">
        <span className="text-slate-400 font-semibold">Single Gateway Abstraction Layer:</span>
        <span className="text-emerald-400 font-mono">100% Provider-Independent</span>
      </div>
    </div>
  );
}
