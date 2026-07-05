const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// Helper function to fetch with auth
export async function fetchWithAuth(
  url: string,
  options: RequestInit = {}
) {
  // We'll use httpOnly cookies, so we need to set credentials: 'include'
  // For now, let's use localStorage as a fallback (but we should use httpOnly cookies in production!)
  const token = localStorage.getItem("token");
  console.log("Token from localStorage:", token);

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string>),
  };
  console.log("Request headers:", headers);

  const fullUrl = `${API_BASE_URL}${url}`;
  console.log("Request URL:", fullUrl);

  const response = await fetch(fullUrl, {
    ...options,
    headers,
  });

  console.log("Response status:", response.status, "for URL:", fullUrl);

  if (!response.ok) {
    // If 401, redirect to login
    if (response.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    throw new Error(`API error: ${response.status} (${response.statusText})`);
  }

  return response;
}

// Auth API
export async function register(email: string, password: string) {
  const res = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return res.json();
}

export async function login(email: string, password: string) {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (data.access_token) {
    localStorage.setItem("token", data.access_token);
  }
  return data;
}

// Projects API
export async function getProjects() {
  const res = await fetchWithAuth("/projects");
  return res.json();
}

export async function createProject(title: string, description?: string) {
  const res = await fetchWithAuth("/projects", {
    method: "POST",
    body: JSON.stringify({ title, description }),
  });
  return res.json();
}

export async function generateProject(projectId: number, idea: string) {
  const res = await fetchWithAuth(`/projects/${projectId}/generate`, {
    method: "POST",
    body: JSON.stringify({ idea }),
  });
  return res.json();
}

export async function getProjectStatus(projectId: number) {
  const res = await fetchWithAuth(`/projects/${projectId}/status`);
  return res.json();
}

export async function downloadProject(projectId: number) {
  const res = await fetchWithAuth(`/projects/${projectId}/download`);
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `project_${projectId}.zip`;
  a.click();
  window.URL.revokeObjectURL(url);
}
