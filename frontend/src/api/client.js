const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? `Request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export function listCases() {
  return request("/api/cases");
}

export function createCase(title) {
  return request("/api/cases", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

export function getCase(caseId) {
  return request(`/api/cases/${caseId}`);
}

export function updateCaseTitle(caseId, title) {
  return request(`/api/cases/${caseId}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });
}

export function deleteCase(caseId) {
  return request(`/api/cases/${caseId}`, {
    method: "DELETE",
  });
}

export function sendMessage(caseId, content) {
  return request(`/api/cases/${caseId}/messages`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}
