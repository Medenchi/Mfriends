const state = {
  me: null,
  socket: null,
  currentChatId: null,
  peer: null,
  localStream: null,
  typingTimer: null,
};

const dictionaries = {
  mode: {
    both: "онлайн + офлайн",
    online: "онлайн",
    offline: "офлайн",
  },
  friendship: {
    both: "временная + постоянная",
    temporary: "временная",
    permanent: "постоянная",
  },
  status: {
    pending: "ожидает",
    accepted: "принята",
    declined: "отклонена",
    blocked: "заблокирована",
    allowed: "разрешено",
  },
  category: {
    gaming: "игры",
    coding: "кодинг",
    studying: "учёба",
    watch_together: "совместный просмотр",
    language_practice: "практика языка",
    walking: "прогулки",
    sports: "спорт",
    cafes: "кафе",
    board_games: "настолки",
    events: "события",
  },
  badge: {
    none: "без бейджа",
  },
  role: {
    user: "пользователь",
    moderator: "модератор",
    admin: "админ",
  },
};

function translate(kind, value, fallback = "") {
  return dictionaries[kind]?.[value] || value || fallback;
}

function $(selector) {
  return document.querySelector(selector);
}

function htmlEscape(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function setView(viewId) {
  document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
  document.querySelectorAll(".sidebar a").forEach((link) => link.classList.remove("active"));
  $(`#${viewId}`).classList.add("active");
  document.querySelector(`[data-view="${viewId}"]`)?.classList.add("active");
}

async function loadMe() {
  state.me = await api("/profiles/me");
  $("#profile-name").value = state.me.display_name || "";
  $("#profile-username").value = state.me.username || "";
  $("#profile-bio").value = state.me.bio || "";
  $("#profile-city").value = state.me.city || "";
  $("#profile-district").value = state.me.district || "";
  $("#profile-mode").value = state.me.online_offline_preference || "both";
  $("#profile-friendship").value = state.me.friendship_preference || "both";
  $("#profile-goals").value = state.me.buddy_goals || "";
  $("#profile-interests").value = state.me.interests || "";
  $("#profile-games").value = state.me.games || "";
  $("#profile-hobbies").value = state.me.hobbies || "";
  $("#avatar-preview").src = state.me.avatar_url || "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80'%3E%3Crect width='80' height='80' fill='%23272735'/%3E%3Ctext x='40' y='48' fill='%23ededf3' text-anchor='middle' font-size='24'%3EM%3C/text%3E%3C/svg%3E";
  $("#me-summary").innerHTML = `
    <span class="pill">trust ${state.me.trust_score || 50}/100</span>
    <span class="pill">${htmlEscape(translate("badge", state.me.verification_badge, "без бейджа"))}</span>
    <p>${htmlEscape(state.me.email)} · ${state.me.is_email_verified ? "email подтверждён" : "email ожидает подтверждения"} · роль ${htmlEscape(translate("role", state.me.role))}</p>
  `;
}

async function loadPeople() {
  const params = new URLSearchParams({
    q: $("#people-query").value,
    interests: $("#people-interests").value,
    games: $("#people-games").value,
    city: $("#people-city").value,
    district: $("#people-district").value,
    mode: $("#people-mode").value,
    verified_only: $("#people-verified").checked ? "true" : "false",
  });
  const data = await api(`/profiles/discover?${params}`);
  $("#people-list").innerHTML = data.people.map((person) => `
    <article class="person">
      <div class="row">
        <h3>${htmlEscape(person.display_name)}</h3>
        <span class="pill">${htmlEscape(translate("mode", person.online_offline_preference))}</span>
        <span class="pill">trust ${person.trust_score || 50}</span>
      </div>
      <p>${htmlEscape(person.bio || "Пока без описания")}</p>
      <p class="mono">${htmlEscape(person.city || "удалённо")} ${person.district ? "· " + htmlEscape(person.district) : ""} · ${htmlEscape(translate("badge", person.verification_badge, "без бейджа"))}</p>
      <p>${htmlEscape([person.interests, person.games, person.hobbies].filter(Boolean).join(" · "))}</p>
      <button class="ghost" data-request="${person.user_id}">Отправить заявку</button>
    </article>
  `).join("");
}

async function loadRequests() {
  const data = await api("/requests");
  $("#request-list").innerHTML = data.requests.map((request) => `
    <article class="request">
      <div class="row"><h3>${htmlEscape(request.title || request.sender_name || `Пользователь #${request.sender_id}`)}</h3><span class="pill">${htmlEscape(translate("mode", request.mode))}</span><span class="pill">${htmlEscape(translate("category", request.category))}</span></div>
      <p>${htmlEscape(request.description || request.message)}</p>
      <p class="mono">${htmlEscape(request.tags)} · ${htmlEscape(translate("status", request.status))} ${request.reward ? "· награда: " + htmlEscape(request.reward) : ""}</p>
      ${request.sender_id !== state.me.user_id && request.status === "pending" ? `
        <button class="primary" data-answer="${request.id}:accepted">Принять</button>
        <button class="secondary" data-answer="${request.id}:declined">Отклонить</button>
      ` : ""}
    </article>
  `).join("");
}

async function loadChats() {
  const data = await api("/chats");
  $("#chat-list").innerHTML = data.chats.map((chat) => `
    <button class="ghost" data-chat="${chat.id}">Чат #${chat.id} · ${htmlEscape(chat.members || "участники")}</button>
  `).join("");
}

async function openChat(chatId) {
  state.currentChatId = chatId;
  state.socket?.send(JSON.stringify({ event: "chat.join", chat_id: chatId }));
  const data = await api(`/chats/${chatId}/messages`);
  $("#messages").innerHTML = data.messages.map((message) => `
    <div class="message ${message.sender_id === state.me.user_id ? "mine" : ""}">
      <strong>${htmlEscape(message.sender_name)}</strong>
      <p>${htmlEscape(message.body)}</p>
      ${message.attachment_url ? `<img class="attachment-preview" src="${htmlEscape(message.attachment_url)}" alt="attachment">` : ""}
      ${message.voice_placeholder ? `<p class="notice">Плейсхолдер голосового сообщения</p>` : ""}
      <span class="mono">${htmlEscape(translate("status", message.moderation_status, message.moderation_status))}</span>
    </div>
  `).join("");
}

function connectSocket() {
  if (!session.token) return;
  state.socket = new WebSocket(`${WS_BASE}?token=${encodeURIComponent(session.token)}`);
  state.socket.addEventListener("message", async (event) => {
    const message = JSON.parse(event.data);
    if (message.event === "chat.message" && Number(message.chat_id) === state.currentChatId) {
      await openChat(state.currentChatId);
    }
    if (message.event === "chat.typing" && Number(message.chat_id) === state.currentChatId && Number(message.from) !== state.me.user_id) {
      $("#typing-status").textContent = message.is_typing ? `Пользователь #${message.from} печатает...` : "";
    }
    if (message.event.startsWith("webrtc.")) {
      await handleSignal(message);
    }
  });
}

async function sendChatMessage(event) {
  event.preventDefault();
  const body = $("#message-body").value.trim();
  if (!body || !state.currentChatId) return;
  let attachmentUrl = null;
  const file = $("#message-image").files[0];
  if (file) {
    const uploaded = await upload("/uploads", file);
    attachmentUrl = uploaded.url;
  }
  await api(`/chats/${state.currentChatId}/messages`, {
    method: "POST",
    body: JSON.stringify({
      chat_id: state.currentChatId,
      body,
      attachment_url: attachmentUrl,
      voice_placeholder: $("#voice-placeholder").checked,
    }),
  });
  state.socket?.send(JSON.stringify({ event: "chat.message", chat_id: state.currentChatId, body }));
  $("#message-body").value = "";
  $("#message-image").value = "";
  $("#voice-placeholder").checked = false;
  await openChat(state.currentChatId);
}

async function startCall() {
  const remoteUserId = Number($("#call-user-id").value);
  if (!remoteUserId) return;
  state.localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
  $("#local-video").srcObject = state.localStream;
  state.peer = createPeer(remoteUserId);
  state.localStream.getTracks().forEach((track) => state.peer.addTrack(track, state.localStream));
  const offer = await state.peer.createOffer();
  await state.peer.setLocalDescription(offer);
  state.socket.send(JSON.stringify({
    event: "webrtc.offer",
    to_user_id: remoteUserId,
    call_id: crypto.randomUUID(),
    payload: offer,
  }));
}

function createPeer(remoteUserId) {
  const peer = new RTCPeerConnection({
    iceServers: [
      { urls: "stun:stun.l.google.com:19302" },
    ],
  });
  peer.onicecandidate = (event) => {
    if (event.candidate) {
      state.socket.send(JSON.stringify({
        event: "webrtc.ice",
        to_user_id: remoteUserId,
        payload: event.candidate,
      }));
    }
  };
  peer.ontrack = (event) => {
    $("#remote-video").srcObject = event.streams[0];
  };
  return peer;
}

async function handleSignal(message) {
  const fromUserId = Number(message.from_user_id);
  if (message.event === "webrtc.offer") {
    state.localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    $("#local-video").srcObject = state.localStream;
    state.peer = createPeer(fromUserId);
    state.localStream.getTracks().forEach((track) => state.peer.addTrack(track, state.localStream));
    await state.peer.setRemoteDescription(message.payload);
    const answer = await state.peer.createAnswer();
    await state.peer.setLocalDescription(answer);
    state.socket.send(JSON.stringify({
      event: "webrtc.answer",
      to_user_id: fromUserId,
      call_id: message.call_id,
      payload: answer,
    }));
  } else if (message.event === "webrtc.answer") {
    await state.peer?.setRemoteDescription(message.payload);
  } else if (message.event === "webrtc.ice") {
    await state.peer?.addIceCandidate(message.payload);
  }
}

async function loadSafetySummary() {
  const data = await api("/moderation/safety-summary");
  $("#safety-summary").innerHTML = `
    <article class="admin-card"><h3>Trust score / доверие</h3><pre>${htmlEscape(JSON.stringify(data.trust_score, null, 2))}</pre></article>
    <article class="admin-card"><h3>Предупреждения</h3>${data.warnings.map((warning) => `<p>${htmlEscape(warning)}</p>`).join("")}</article>
    <article class="admin-card"><h3>Недавняя модерация</h3><pre>${htmlEscape(JSON.stringify(data.recent, null, 2))}</pre></article>
  `;
}

async function loadAdmin() {
  const [queue, analytics] = await Promise.all([api("/moderation/admin/queue"), api("/moderation/admin/analytics")]);
  $("#admin-content").innerHTML = `
    <article class="admin-card"><h3>Аналитика</h3><pre>${htmlEscape(JSON.stringify(analytics, null, 2))}</pre></article>
    <article class="admin-card"><h3>Жалобы</h3><pre>${htmlEscape(JSON.stringify(queue.reports, null, 2))}</pre></article>
    <article class="admin-card"><h3>Подозрительные пользователи</h3><pre>${htmlEscape(JSON.stringify(queue.suspicious_users, null, 2))}</pre></article>
    <article class="admin-card"><h3>AI-логи</h3><pre>${htmlEscape(JSON.stringify(queue.ai_moderation_logs, null, 2))}</pre></article>
    <article class="admin-card"><h3>Проверка верификаций</h3><pre>${htmlEscape(JSON.stringify(queue.verification_review, null, 2))}</pre></article>
  `;
}

function bindApp() {
  document.querySelectorAll(".sidebar a").forEach((link) => {
    link.addEventListener("click", async (event) => {
      event.preventDefault();
      setView(link.dataset.view);
      if (link.dataset.view === "safety") await loadSafetySummary();
    });
  });
  $("#discover-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await loadPeople();
  });
  $("#profile-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await api("/profiles/me", {
      method: "PUT",
      body: JSON.stringify({
        display_name: $("#profile-name").value,
        username: $("#profile-username").value,
        bio: $("#profile-bio").value,
        city: $("#profile-city").value,
        district: $("#profile-district").value,
        buddy_goals: $("#profile-goals").value,
        interests: $("#profile-interests").value,
        games: $("#profile-games").value,
        hobbies: $("#profile-hobbies").value,
        online_offline_preference: $("#profile-mode").value,
        friendship_preference: $("#profile-friendship").value,
      }),
    });
    await loadMe();
  });
  $("#avatar-file").addEventListener("change", async () => {
    const file = $("#avatar-file").files[0];
    if (!file) return;
    await upload("/uploads/avatar", file);
    await loadMe();
  });
  $("#people-list").addEventListener("click", async (event) => {
    const userId = event.target.dataset.request;
    if (!userId) return;
    await api("/requests", {
      method: "POST",
      body: JSON.stringify({ receiver_id: Number(userId), request_type: "friend", title: "Заявка в друзья", message: "Давай законнектимся в MFriends." }),
    });
    await loadRequests();
    setView("requests");
  });
  $("#request-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await api("/requests", {
      method: "POST",
      body: JSON.stringify({
        title: $("#request-title").value,
        description: $("#request-description").value,
        message: $("#request-description").value,
        category: $("#request-category").value,
        mode: $("#request-mode").value,
        tags: $("#request-tags").value,
        reward: $("#request-reward").value,
      }),
    });
    event.target.reset();
    await loadRequests();
  });
  $("#request-list").addEventListener("click", async (event) => {
    const answer = event.target.dataset.answer;
    if (!answer) return;
    const [requestId, decision] = answer.split(":");
    await api(`/requests/${requestId}/${decision}`, { method: "POST" });
    await loadRequests();
    await loadChats();
  });
  $("#chat-list").addEventListener("click", async (event) => {
    const chatId = event.target.dataset.chat;
    if (chatId) await openChat(Number(chatId));
  });
  $("#message-body").addEventListener("input", () => {
    if (!state.currentChatId) return;
    state.socket?.send(JSON.stringify({ event: "chat.typing", chat_id: state.currentChatId, is_typing: true }));
    clearTimeout(state.typingTimer);
    state.typingTimer = setTimeout(() => state.socket?.send(JSON.stringify({ event: "chat.typing", chat_id: state.currentChatId, is_typing: false })), 900);
  });
  $("#message-form").addEventListener("submit", sendChatMessage);
  $("#call-start").addEventListener("click", startCall);
  document.querySelectorAll("[data-verify]").forEach((button) => {
    button.addEventListener("click", async () => {
      const result = await api("/verification/start", { method: "POST", body: JSON.stringify({ verification_type: button.dataset.verify }) });
      $("#verification-result").textContent = JSON.stringify(result, null, 2);
    });
  });
  $("#report-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await api("/moderation/reports", { method: "POST", body: JSON.stringify({ reported_user_id: Number($("#report-user-id").value), reason: $("#report-reason").value, details: $("#report-details").value }) });
    await loadSafetySummary();
  });
  $("#block-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await api("/moderation/blocks", { method: "POST", body: JSON.stringify({ blocked_user_id: Number($("#block-user-id").value), reason: "Заблокировано из панели безопасности" }) });
    await loadSafetySummary();
  });
  $("#admin-load").addEventListener("click", loadAdmin);
  $("#logout").addEventListener("click", () => {
    session.clear();
    location.href = "login.html";
  });
}

async function bootApp() {
  if (!session.token) {
    location.href = "login.html";
    return;
  }
  bindApp();
  connectSocket();
  await loadMe();
  await Promise.all([loadPeople(), loadRequests(), loadChats()]);
}
