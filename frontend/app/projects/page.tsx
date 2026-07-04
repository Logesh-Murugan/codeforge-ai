"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getProjects, createProject, generateProject } from "@/lib/api";

interface Project {
  id: number;
  title: string;
  description?: string;
  created_at: string;
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [title, setTitle] = useState("");
  const [idea, setIdea] = useState("");
  const [creating, setCreating] = useState(false);
  const router = useRouter();

  useEffect(() => {
    async function loadProjects() {
      try {
        const data = await getProjects();
        setProjects(data);
      } catch (err) {
        console.error("Failed to load projects", err);
      } finally {
        setLoading(false);
      }
    }
    loadProjects();
  }, []);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      const project = await createProject(title, idea);
      await generateProject(project.id, idea);
      router.push(`/projects/${project.id}`);
    } catch (err: unknown) {
      console.error(err);
    } finally {
      setCreating(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/login");
  };

  if (loading) {
    return (
      <div className="min-h-screen gradient-bg flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-12 h-12 rounded-xl border-t-2 border-indigo-500 border-r-2 border-r-transparent animate-spin" />
          <p className="text-gray-400 text-sm">Loading workspace projects...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen gradient-bg flex flex-col justify-between">
      {/* Background decoration */}
      <div className="absolute top-0 right-0 w-[30rem] h-[30rem] bg-indigo-900/10 rounded-full blur-[100px] pointer-events-none" />

      {/* Header */}
      <header className="w-full border-b border-white/5 bg-black/20 backdrop-blur-md sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-base shadow-lg shadow-indigo-500/25">
              CF
            </div>
            <span className="font-extrabold text-base tracking-tight text-white">
              CodeForge <span className="text-indigo-400">AI</span>
            </span>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl text-sm font-semibold shadow-lg shadow-indigo-600/30 transition-all"
            >
              {showCreateForm ? "View My Projects" : "+ New Project"}
            </button>
            <button
              onClick={handleLogout}
              className="text-gray-400 hover:text-white text-sm font-semibold transition-colors"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Main dashboard content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-10 z-10">
        {showCreateForm ? (
          <div className="max-w-3xl mx-auto">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h1 className="text-2xl font-bold text-white mb-1">Create New Project</h1>
                <p className="text-xs text-gray-400">Configure your backend requirements for the AI pipeline</p>
              </div>
              <button
                onClick={() => setShowCreateForm(false)}
                className="text-gray-400 hover:text-white text-sm font-semibold transition-colors"
              >
                ← Cancel
              </button>
            </div>

            <div className="glass-panel rounded-3xl p-8 border-white/5 relative overflow-hidden shadow-2xl">
              <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-indigo-500/30 to-transparent" />
              
              <form onSubmit={handleCreateProject} className="space-y-6">
                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                    Project Title
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/80 transition-all text-sm"
                    placeholder="E.g. TaskList API, E-Commerce Store Backend"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                    Project Idea & Description
                  </label>
                  <textarea
                    value={idea}
                    onChange={(e) => setIdea(e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/80 transition-all text-sm h-48 resize-none"
                    placeholder="Describe what your backend should do. Mention database entities, their columns, relationships, actions, and whether JWT authentication is required for endpoints."
                    required
                  />
                  <div className="mt-3 bg-indigo-950/20 border border-indigo-500/20 rounded-xl p-4 text-xs text-indigo-300">
                    <span className="font-bold uppercase tracking-wider block mb-1">💡 Prompt Tip</span>
                    &quot;A task list manager where users can register/login, create projects, tasks inside those projects with titles and priorities. Ensure users can only see and delete their own tasks.&quot;
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={creating}
                  className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white py-3.5 px-4 rounded-xl font-bold text-sm shadow-lg shadow-indigo-500/20 hover:scale-[1.01] active:scale-[0.99] transition-all disabled:opacity-50 disabled:pointer-events-none"
                >
                  {creating ? "Spinning up 5 Agents..." : "Start Agent Generation"}
                </button>
              </form>
            </div>
          </div>
        ) : (
          <div className="max-w-6xl mx-auto">
            <div className="flex justify-between items-center mb-8">
              <div>
                <h1 className="text-3xl font-extrabold text-white mb-1">Development Workspace</h1>
                <p className="text-xs text-gray-400">Manage and monitor your generated backend projects</p>
              </div>
              <div className="flex items-center space-x-3">
                <span className="bg-white/5 text-gray-400 px-3 py-1.5 rounded-xl text-xs border border-white/5">
                  Total Projects: <span className="text-white font-bold">{projects.length}</span>
                </span>
              </div>
            </div>

            {projects.length === 0 ? (
              <div className="glass-panel rounded-3xl p-12 text-center border-white/5 max-w-2xl mx-auto mt-10">
                <div className="w-16 h-16 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center font-bold text-2xl text-indigo-400 mx-auto mb-6">
                  🛠️
                </div>
                <h2 className="text-xl font-bold text-white mb-2">No projects found</h2>
                <p className="text-gray-400 text-sm mb-6 max-w-md mx-auto">
                  You haven&apos;t generated any backend codebases yet. Let&apos;s describe your first API idea and watch our agent pipeline build it!
                </p>
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white px-6 py-3 rounded-xl font-bold text-sm shadow-lg transition-all"
                >
                  Create Your First Project
                </button>
              </div>
            ) : (
              <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                {projects.map((project) => (
                  <div
                    key={project.id}
                    onClick={() => router.push(`/projects/${project.id}`)}
                    className="glass-panel glass-panel-hover rounded-3xl p-6 cursor-pointer border-white/5 flex flex-col justify-between h-[220px]"
                  >
                    <div>
                      <div className="flex justify-between items-start mb-3">
                        <h2 className="text-lg font-bold text-white group-hover:text-indigo-400 transition-colors line-clamp-1">
                          {project.title}
                        </h2>
                        <span className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/25 text-[10px] px-2 py-0.5 rounded font-semibold">
                          ID: {project.id}
                        </span>
                      </div>
                      {project.description && (
                        <p className="text-xs text-gray-400 line-clamp-4 leading-relaxed">
                          {project.description}
                        </p>
                      )}
                    </div>
                    <div className="mt-4 pt-4 border-t border-white/5 flex justify-between items-center text-[10px] text-gray-500">
                      <span>Created</span>
                      <span className="font-semibold text-gray-400">
                        {new Date(project.created_at).toLocaleDateString()} at {new Date(project.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-white/5 bg-black/20 backdrop-blur-md py-6 z-10">
        <div className="max-w-7xl mx-auto px-6 text-center text-xs text-gray-500">
          © {new Date().getFullYear()} CodeForge AI. All rights reserved.
        </div>
      </footer>
    </div>
  );
}
