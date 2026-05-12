const API_BASE = window.MFRIENDS_API_BASE || (location.hostname === "mfriends.denchy.cyou" ? "https://api.denchy.cyou" : "/api");
const WS_BASE = window.MFRIENDS_WS_BASE || (location.hostname === "mfriends.denchy.cyou" ? "wss://ws.denchy.cyou/ws" : `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`);

const session = {
  get token() {
    return localStorage.getItem("mfriends_access_token");
  },
  set token(value) {
    localStorage.setItem("mfriends_access_token", value);
  },
  clear() {
    localStorage.removeItem("mfriends_access_token");
    localStorage.removeItem("mfriends_refresh_token");
  },
};

async function api(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (session.token) {
    headers.Authorization = `Bearer ${session.token}`;
  }
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data;
}

async function upload(path, file) {
  const body = new FormData();
  body.append("file", file);
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${session.token}`,
    },
    body,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Upload failed");
  }
  return data;
}

function bindAuthForms() {
  const registerForm = document.querySelector("#register-form");
  const loginForm = document.querySelector("#login-form");
  const resetRequestForm = document.querySelector("#reset-request-form");
  const resetConfirmForm = document.querySelector("#reset-confirm-form");
  if (registerForm) {
    registerForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(registerForm);
      const result = await api("/auth/register", {
        method: "POST",
        body: JSON.stringify(Object.fromEntries(form.entries())),
      });
      session.token = result.access_token;
      localStorage.setItem("mfriends_refresh_token", result.refresh_token);
      location.href = "app.html";
    });
  }
  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(loginForm);
      const result = await api("/auth/login", {
        method: "POST",
        body: JSON.stringify(Object.fromEntries(form.entries())),
      });
      session.token = result.access_token;
      localStorage.setItem("mfriends_refresh_token", result.refresh_token);
      location.href = "app.html";
    });
  }
  if (resetRequestForm) {
    resetRequestForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(resetRequestForm);
      await api("/auth/password-reset/request", { method: "POST", body: JSON.stringify(Object.fromEntries(form.entries())) });
      document.querySelector("#reset-status").textContent = "If the account exists, an email was sent.";
    });
  }
  if (resetConfirmForm) {
    resetConfirmForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(resetConfirmForm);
      const payload = Object.fromEntries(form.entries());
      payload.token = new URLSearchParams(location.search).get("token") || payload.token;
      await api("/auth/password-reset/confirm", { method: "POST", body: JSON.stringify(payload) });
      document.querySelector("#reset-status").textContent = "Password updated. You can log in.";
    });
  }
}
