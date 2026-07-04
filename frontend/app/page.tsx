import Link from "next/link";

export default function Home() {
  const agents = [
    { name: "Business Analyst", desc: "Analyzes the description, identifies data entities and core actions.", model: "llama-3.1-8b", color: "from-blue-500 to-cyan-400" },
    { name: "Solution Architect", desc: "Designs database schemas, REST APIs and files structures.", model: "llama-3.3-70b", color: "from-indigo-500 to-purple-500" },
    { name: "Backend Developer", desc: "Generates the complete FastAPI code with database & secure JWT auth.", model: "llama-3.3-70b", color: "from-purple-500 to-pink-500" },
    { name: "Code Reviewer", desc: "Performs static analysis, reviews security vulnerabilities, auto-fixes style issues.", model: "llama-3.3-70b", color: "from-pink-500 to-rose-500" },
    { name: "Documentation Writer", desc: "Generates project README.md, deployment configuration and developer instructions.", model: "llama-3.1-8b", color: "from-rose-500 to-amber-500" }
  ];

  return (
    <div className="min-h-screen relative overflow-hidden gradient-bg flex flex-col justify-between">
      {/* Background decorations */}
      <div className="absolute top-[-10%] left-[-10%] w-[40rem] h-[40rem] bg-indigo-900/20 rounded-full blur-[120px] animate-pulse-slow pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40rem] h-[40rem] bg-purple-900/20 rounded-full blur-[120px] animate-pulse-slow pointer-events-none" />

      {/* Header */}
      <header className="w-full max-w-7xl mx-auto px-6 py-6 flex justify-between items-center z-10">
        <div className="flex items-center space-x-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-xl shadow-lg shadow-indigo-500/25">
            CF
          </div>
          <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
            CodeForge <span className="text-indigo-400">AI</span>
          </span>
        </div>
        <div className="flex items-center space-x-4">
          <Link href="/login" className="text-gray-300 hover:text-white px-4 py-2 text-sm font-medium transition-colors">
            Sign In
          </Link>
          <Link href="/register" className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-xl text-sm font-semibold shadow-lg shadow-indigo-600/30 transition-all hover:scale-[1.02] active:scale-[0.98]">
            Get Started
          </Link>
        </div>
      </header>

      {/* Main Hero */}
      <main className="flex-1 flex flex-col items-center justify-center max-w-7xl mx-auto px-6 py-12 z-10 w-full">
        <div className="text-center max-w-3xl mb-16">
          <div className="inline-flex items-center space-x-2 bg-indigo-950/50 border border-indigo-500/30 px-3 py-1.5 rounded-full mb-6 text-indigo-300 text-xs font-semibold uppercase tracking-wider">
            <span>✨</span> <span>Agentic Coding Workspace v0.1</span>
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 leading-tight">
            Forge Production APIs <br />
            <span className="gradient-text">With 5 AI Agents</span>
          </h1>
          <p className="text-lg md:text-xl text-gray-400 font-normal leading-relaxed mb-8 max-w-2xl mx-auto">
            From a single sentence to a fully-formed FastAPI & PostgreSQL backend. 
            No chatbots. No half-finished snippets. Just download your zip and run.
          </p>
          <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4 justify-center">
            <Link href="/register" className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white px-8 py-4 rounded-xl font-bold text-base shadow-xl shadow-indigo-500/20 transition-all hover:scale-[1.03] active:scale-[0.97]">
              Build Your First API
            </Link>
            <Link href="/login" className="bg-white/5 hover:bg-white/10 text-gray-200 border border-white/10 px-8 py-4 rounded-xl font-bold text-base backdrop-blur-md transition-all hover:scale-[1.03] active:scale-[0.97]">
              Workspace Demo
            </Link>
          </div>
        </div>

        {/* Pipeline visualizer preview */}
        <div className="w-full">
          <h2 className="text-2xl font-bold text-center text-gray-300 mb-10">
            How the Agent Pipeline Works
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {agents.map((agent, i) => (
              <div key={i} className="glass-panel glass-panel-hover rounded-2xl p-6 flex flex-col justify-between min-h-[220px]">
                <div>
                  <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${agent.color} flex items-center justify-center font-bold text-sm text-black mb-4`}>
                    {i + 1}
                  </div>
                  <h3 className="text-lg font-bold text-white mb-2 leading-snug">
                    {agent.name}
                  </h3>
                  <p className="text-xs text-gray-400 leading-relaxed">
                    {agent.desc}
                  </p>
                </div>
                <div className="mt-4 pt-4 border-t border-white/5 flex justify-between items-center text-[10px]">
                  <span className="text-gray-500 uppercase font-semibold">Model</span>
                  <span className="bg-white/5 text-gray-300 px-2 py-0.5 rounded border border-white/10">{agent.model}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-white/5 bg-black/20 backdrop-blur-md py-6 z-10">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center text-sm text-gray-500">
          <div>
            © {new Date().getFullYear()} CodeForge AI. All rights reserved.
          </div>
          <div className="flex space-x-6 mt-4 md:mt-0">
            <a href="#" className="hover:text-gray-400 transition-colors">Documentation</a>
            <a href="#" className="hover:text-gray-400 transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-gray-400 transition-colors">GitHub</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
