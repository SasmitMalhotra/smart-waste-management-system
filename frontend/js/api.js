// Shared API helper used by every page.
// Change API_BASE if the Flask backend runs somewhere other than localhost:5000.
const API_BASE = "http://localhost:5000/api";

const Auth = {
  getToken: () => localStorage.getItem("swms_token"),
  getUser: () => JSON.parse(localStorage.getItem("swms_user") || "null"),
  setSession: (token, user) => {
    localStorage.setItem("swms_token", token);
    localStorage.setItem("swms_user", JSON.stringify(user));
  },
  clearSession: () => {
    localStorage.removeItem("swms_token");
    localStorage.removeItem("swms_user");
  },
  requireAuth: (allowedRoles) => {
    const token = Auth.getToken();
    const user = Auth.getUser();
    if (!token || !user) {
      window.location.replace("/index.html");
      return null;
    }
    if (allowedRoles && !allowedRoles.includes(user.role)) {
      window.location.replace("/index.html");
      return null;
    }
    return user;
  },
  logout: () => {
    Auth.clearSession();
    window.location.replace("/index.html");
  },
};

async function apiRequest(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = Auth.getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data = null;
  try {
    data = await res.json();
  } catch (e) {
    /* no JSON body */
  }

  if (!res.ok) {
    const message = (data && data.error) || `Request failed (${res.status})`;
    throw new Error(message);
  }
  return data;
}

function showToast(message) {
  let toast = document.querySelector(".toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => toast.classList.remove("show"), 2800);
}

function fillBarClass(level) {
  if (level >= 90) return "danger";
  if (level >= 70) return "warn";
  return "";
}

function formatDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}