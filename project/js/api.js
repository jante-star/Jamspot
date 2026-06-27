// Jamspot API client — loaded into every page via bundle injection

window.JamSpot = window.JamSpot || {};

JamSpot.session = null;

async function apiFetch(path, options = {}) {
  const res = await fetch(path, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
    body: options.body && typeof options.body === 'object' ? JSON.stringify(options.body) : options.body,
  });
  let data;
  try { data = await res.json(); } catch { data = {}; }
  if (!res.ok) throw Object.assign(new Error(data.error || 'Request failed'), { status: res.status, data });
  return data;
}

async function getSession(force = false) {
  if (JamSpot.session && !force) return JamSpot.session;
  try {
    const data = await apiFetch('/api/auth/me');
    JamSpot.session = data;
    return data;
  } catch {
    JamSpot.session = { authenticated: false };
    return JamSpot.session;
  }
}

function requireAuth(redirectTo = '/auth.html') {
  return getSession().then(s => {
    if (!s.authenticated) window.location.href = redirectTo;
    return s;
  });
}

function getParam(key) {
  return new URLSearchParams(window.location.search).get(key) || '';
}

JamSpot.apiFetch = apiFetch;
JamSpot.getSession = getSession;
JamSpot.requireAuth = requireAuth;
JamSpot.getParam = getParam;
