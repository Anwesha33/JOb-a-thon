// Thin wrapper around the backend API. All paths are relative so the Vite
// dev-server proxy (and a same-origin production build) route them to FastAPI.

async function req(path, options = {}) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch (_) {
      /* body wasn't JSON */
    }
    throw new Error(detail);
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  health: () => req("/api/health"),

  uploadResume: (file) => {
    const form = new FormData();
    form.append("file", file);
    return req("/api/resume/upload", { method: "POST", body: form });
  },

  search: (payload) =>
    req("/api/opportunities/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  listOpportunities: () => req("/api/opportunities"),
  budget: () => req("/api/opportunities/budget"),

  resolveQuestion: (payload) =>
    req("/api/questions/resolve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  answerQuestion: (question, answer) =>
    req("/api/questions/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, answer }),
    }),

  startApply: (payload) =>
    req("/api/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  applyStatus: (jobId) => req(`/api/apply/${jobId}`),

  applyLink: (url, profileId) =>
    req("/api/apply/link", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, profile_id: profileId }),
    }),

  listApplications: () => req("/api/applications"),

  updateApplicationStatus: (opportunityId, status) =>
    req(`/api/applications/${opportunityId}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    }),
};
