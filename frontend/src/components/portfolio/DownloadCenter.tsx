"use client";

import React from "react";

interface DownloadArtifact {
  artifact_name: string;
  file_type: string;
  download_url: string;
  file_size_kb: float;
}

interface DownloadCenterProps {
  downloads: DownloadArtifact[];
}

export const DownloadCenter: React.FC<DownloadCenterProps> = ({ downloads }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl mt-6">
      <h3 className="text-lg font-bold text-white mb-4">Portfolio Download Center</h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {downloads.map((d, i) => (
          <div key={i} className="flex items-center justify-between bg-slate-800/40 p-4 rounded-lg border border-slate-700/40 text-xs">
            <div>
              <span className="font-bold text-white block">{d.artifact_name}</span>
              <span className="text-slate-400">{d.file_type} • {d.file_size_kb} KB</span>
            </div>
            <a
              href={`http://localhost:8000${d.download_url}`}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-blue-600 hover:bg-blue-500 text-white font-semibold px-3 py-1.5 rounded transition"
            >
              Download
            </a>
          </div>
        ))}
      </div>
    </div>
  );
};
