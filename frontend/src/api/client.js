const API_BASE = import.meta.env.VITE_API_BASE || "";

function headers(token) {
  const h = { "Content-Type": "application/json" };
  if (token) h["Authorization"] = `Bearer ${token}`;
  return h;
}

async function handle(res) {
  if (!res.ok) {
    let body = {};
    try { body = await res.json(); } catch {}
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  createRoom: (payload) =>
    fetch(`${API_BASE}/api/rooms`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify(payload),
    }).then(handle),

  joinRoom: (code, name) =>
    fetch(`${API_BASE}/api/rooms/${code}/join`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ name }),
    }).then(handle),

  getRoom: (code) =>
    fetch(`${API_BASE}/api/rooms/${code}`).then(handle),

  start: (code, token, algorithm) =>
    fetch(`${API_BASE}/api/rooms/${code}/start`, {
      method: "POST",
      headers: headers(token),
      body: JSON.stringify({ algorithm }),
    }).then(handle),

  startVoting: (code, token) =>
    fetch(`${API_BASE}/api/rooms/${code}/vote-phase`, {
      method: "POST",
      headers: headers(token),
    }).then(handle),

  resolve: (code, token) =>
    fetch(`${API_BASE}/api/rooms/${code}/resolve`, {
      method: "POST",
      headers: headers(token),
    }).then(handle),

  reset: (code, token) =>
    fetch(`${API_BASE}/api/rooms/${code}/reset`, {
      method: "POST",
      headers: headers(token),
    }).then(handle),

  addOption: (code, token, text) =>
    fetch(`${API_BASE}/api/rooms/${code}/options`, {
      method: "POST",
      headers: headers(token),
      body: JSON.stringify({ text }),
    }).then(handle),

  deleteOption: (code, token, optionId) =>
    fetch(`${API_BASE}/api/rooms/${code}/options/${optionId}`, {
      method: "DELETE",
      headers: headers(token),
    }).then(handle),

  castVote: (code, token, optionId, kind, isDealbreaker) =>
    fetch(`${API_BASE}/api/rooms/${code}/votes`, {
      method: "POST",
      headers: headers(token),
      body: JSON.stringify({
        option_id: optionId,
        kind,
        is_dealbreaker: isDealbreaker,
      }),
    }).then(handle),
};
