import Link from "next/link";

export default function Home() {
  const agents = [
    { name: "Project Manager", role: "Milestones & Scope", model: "llama-3.3-70b", color: "from-blue-500 to-cyan-400" },
    { name: "Business Analyst", role: "Requirements & Entities", model: "llama-3.1-8b", color: "from-cyan-400 to-teal-400" },
    { name: "Product Owner", role: "Backlog & Acceptance Criteria", model: "llama-3.1-8b", color: "from-teal-400 to-emerald-400" },
    { name: "Solution Architect", role: "System Architecture", model: "llama-3.3-70b", color: "from-indigo-500 to-purple-500" },
    { name: "Database Engineer", role: "ERD & SQLAlchemy Models", model: "llama-3.3-70b", color: "from-purple-500 to-fuchsia-500" },
    { name: "API Designer", role: "OpenAPI 3.1 & Auth Specs", model: "llama-3.3-70b", color: "from-fuchsia-500 to-pink-500" },
    { name: "Backend Developer", role: "FastAPI REST Codebase", model: "llama-3.3-70b", color: "from-pink-500 to-rose-500" },
    { name: "Security Engineer", role: "OWASP & JWT Hardening", model: "llama-3.3-70b", color: "from-rose-500 to-red-500" },
    { name: "QA Engineer", role: "Unit & Integration Tests", model: "llama-3.3-70b", color: "from-amber-500 to-orange-500" },
    { name: "Frontend Developer", role: "Next.js & Tailwind UI", model: "llama-3.3-70b", color: "from-yellow-400 to-amber-500" },
    { name: "Code Reviewer", role: "Static Analysis & Auto-Fix", model: "llama-3.3-70b", color: "from-emerald-500 to-green-500" },
    { name: "Doc Writer", role: "README & API Guides", model: "llama-3.1-8b", color: "from-green-400 to-teal-500" },
    { name: "DevOps Engineer", role: "Dockerfile & CI/CD Pipelines", model: "llama-3.3-70b", color: "from-blue-600 to-indigo-600" }
  ];

  const features = [
    { title: "13-Agent Orchestrator", desc: "Deterministic LangGraph state machine driving a simulated 13-role engineering team.", icon: "🤖" },
    { title: "Hybrid AI Mode Manager", desc: "Hot-swap seamlessly between local Ollama models and cloud Groq inference engines.", icon: "🔄" },
    { title: "Hybrid RAG & Vector Memory", desc: "ChromaDB dense search combined with BM25 sparse keyword ranking across 12 memory collections.", icon: "🧠" },
    { title: "Real-Time Telemetry Stream", desc: "Live WebSocket monitoring, event streaming, metrics engine, and live log viewer.", icon: "⚡" },
    { title: "12-Stage Validation Gate", desc: "Automated quality gate inspecting structure, AST syntax, security (OWASP), and performance.", icon: "🛡️" },
    { title: "Timeline & Analytics Engine", desc: "Persistent database tracking, 9 milestone detectors, and runtime performance statistics.", icon: "⏱️" },
    { title: "Portfolio & Mermaid Exporter", desc: "Generates 8 automated Mermaid diagrams, multi-format engineering reports, and ZIP packages.", icon: "📦" },
    { title: "Enterprise Hardened", desc: "Database connection pool recycling, Zip Slip protection, prompt injection filters, and health probes.", icon: "🔒" }
  ];

  return (
    <div className="min-h-screen relative overflow-hidden bg-slate-950 text-white flex flex-col justify-between">
      {/* Background decorations */}
      <div className="absolute top-[-10%] left-[-10%] w-[45rem] h-[45rem] bg-indigo-900/20 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[45rem] h-[45rem] bg-purple-900/20 rounded-full blur-[140px] pointer-events-none" />

      {/* Header */}
      <header className="w-full max-w-7xl mx-auto px-6 py-6 flex justify-between items-center z-10">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center font-extrabold text-xl shadow-lg shadow-indigo-500/25">
            CF
          </div>
          <span className="font-extrabold text-2xl tracking-tight bg-gradient-to-r from-white via-gray-200 to-indigo-300 bg-clip-text text-transparent">
            CodeForge <span className="text-indigo-400">AI</span>
          </span>
          <span className="bg-indigo-500/20 text-indigo-300 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-indigo-500/30">
            v2.0.0
          </span>
        </div>
        <div className="flex items-center space-x-4">
          <Link href="/projects" className="text-gray-300 hover:text-white px-3 py-2 text-sm font-medium transition-colors">
            Projects
          </Link>
          <Link href="/login" className="text-gray-300 hover:text-white px-3 py-2 text-sm font-medium transition-colors">
            Sign In
          </Link>
          <Link href="/register" className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-xl text-sm font-semibold shadow-lg shadow-indigo-600/30 transition-all hover:scale-[1.02] active:scale-[0.98]">
            Get Started
          </Link>
        </div>
      </header>

      {/* Main Hero */}
      <main className="flex-1 flex flex-col items-center justify-center max-w-7xl mx-auto px-6 py-12 z-10 w-full">
        <div className="text-center max-w-4xl mb-16">
          <div className="inline-flex items-center space-x-2 bg-indigo-950/70 border border-indigo-500/40 px-4 py-2 rounded-full mb-6 text-indigo-300 text-xs font-bold uppercase tracking-wider shadow-inner">
            <span>⚡</span> <span>Autonomous Engineering Platform v2.0.0</span>
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 leading-tight">
            Autonomous Software Engineering <br />
            <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">With 13 AI Agents</span>
          </h1>
          <p className="text-lg md:text-xl text-gray-300 font-normal leading-relaxed mb-8 max-w-3xl mx-auto">
            From a single prompt to a production-grade FastAPI & Next.js codebase. 
            Automated architecture design, RAG vector memory, 12-stage validation quality gate, 
            real-time monitoring telemetry, and instant ZIP exports.
          </p>
          <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4 justify-center">
            <Link href="/register" className="bg-gradient-to-r from-indigo-500 via-purple-600 to-pink-600 hover:from-indigo-600 hover:to-pink-700 text-white px-8 py-4 rounded-xl font-bold text-base shadow-xl shadow-indigo-500/25 transition-all hover:scale-[1.03] active:scale-[0.97]">
              Build Your Application
            </Link>
            <Link href="/projects" className="bg-white/10 hover:bg-white/15 text-gray-200 border border-white/15 px-8 py-4 rounded-xl font-bold text-base backdrop-blur-md transition-all hover:scale-[1.03] active:scale-[0.97]">
              Explore Dashboard
            </Link>
          </div>
        </div>

        {/* 13-Agent Orchestrator Pipeline Visualizer */}
        <div className="w-full mb-20">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h2 className="text-3xl font-extrabold text-white">13-Agent LangGraph Pipeline</h2>
              <p className="text-sm text-gray-400 mt-1">Deterministic AI software development team executing sequentially</p>
            </div>
            <span className="text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-3 py-1.5 rounded-lg font-mono">
              13 Agents • 100% Autonomous
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
            {agents.map((agent, i) => (
              <div key={i} className="bg-slate-900/60 border border-white/10 hover:border-indigo-500/50 rounded-xl p-4 flex flex-col justify-between backdrop-blur-md transition-all hover:-translate-y-1">
                <div>
                  <div className={`w-7 h-7 rounded-lg bg-gradient-to-br ${agent.color} flex items-center justify-center font-bold text-xs text-black mb-3`}>
                    {i + 1}
                  </div>
                  <h3 className="text-sm font-bold text-white mb-1 leading-snug">
                    {agent.name}
                  </h3>
                  <p className="text-[11px] text-gray-400 leading-tight">
                    {agent.role}
                  </p>
                </div>
                <div className="mt-3 pt-2 border-t border-white/5 flex justify-between items-center text-[9px]">
                  <span className="text-gray-500 font-mono">LLM</span>
                  <span className="bg-white/5 text-gray-300 px-1.5 py-0.5 rounded border border-white/10 font-mono">{agent.model}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Platform Capabilities Grid */}
        <div className="w-full mb-12">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-extrabold text-white">Enterprise Platform Subsystems</h2>
            <p className="text-sm text-gray-400 mt-2">Comprehensive suite built across 14 architecture development phases</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feat, i) => (
              <div key={i} className="bg-slate-900/70 border border-white/10 hover:border-purple-500/40 rounded-2xl p-6 transition-all hover:bg-slate-900/90">
                <div className="text-3xl mb-4">{feat.icon}</div>
                <h3 className="text-lg font-bold text-white mb-2">{feat.title}</h3>
                <p className="text-xs text-gray-400 leading-relaxed">{feat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-white/10 bg-slate-950/80 backdrop-blur-md py-8 z-10">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center text-sm text-gray-400">
          <div className="flex items-center space-x-2">
            <div className="w-6 h-6 rounded-md bg-indigo-500 flex items-center justify-center font-bold text-xs text-white">
              CF
            </div>
            <span>© {new Date().getFullYear()} CodeForge AI v2.0.0. All rights reserved.</span>
          </div>
          <div className="flex space-x-6 mt-4 md:mt-0 text-xs">
            <Link href="/projects" className="hover:text-white transition-colors">Projects</Link>
            <Link href="/validation" className="hover:text-white transition-colors">Validation Pipeline</Link>
            <Link href="/timeline" className="hover:text-white transition-colors">Timeline</Link>
            <Link href="/portfolio" className="hover:text-white transition-colors">Portfolio</Link>
            <a href="https://github.com/Logesh-Murugan/codeforge-ai" target="_blank" rel="noreferrer" className="hover:text-white transition-colors">GitHub Repository</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
