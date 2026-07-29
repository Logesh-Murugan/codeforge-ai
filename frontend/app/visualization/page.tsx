import AgentPipelineVisualizer from "../../src/components/visualization/AgentPipelineVisualizer";

export default function VisualizationPage() {
  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      <header className="w-full max-w-6xl mx-auto px-6 py-6 flex items-center space-x-2">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-sm shadow-lg shadow-indigo-500/25">
          CF
        </div>
        <span className="font-extrabold text-lg tracking-tight text-white">
          CodeForge <span className="text-indigo-400">AI</span>
        </span>
        <span className="text-sm text-gray-500 ml-2">Agent Visualization</span>
      </header>
      <main className="flex-1 flex items-start justify-center px-6 py-8">
        <AgentPipelineVisualizer darkMode={true} />
      </main>
    </div>
  );
}
