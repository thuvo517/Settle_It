const KEY = "settleit.sessions";

function load() {
  try {
    return JSON.parse(localStorage.getItem(KEY) || "{}");
  } catch {
    return {};
  }
}

function save(all) {
  localStorage.setItem(KEY, JSON.stringify(all));
}

export function saveSession(code, session) {
  const all = load();
  all[code] = session;
  save(all);
}

export function getSession(code) {
  return load()[code] || null;
}

export function clearSession(code) {
  const all = load();
  delete all[code];
  save(all);
}
