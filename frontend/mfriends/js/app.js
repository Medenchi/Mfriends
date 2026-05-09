const state = {
  me: null,
  socket: null,
  currentChatId: null,
  peer: null,
  localStream: null,
};

function $(selector) {
  return document.querySelector(selector);
}

function htmlEscape(value) {
  return String(value)
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
  $("#profile-bio").value = state.me.bio || "";
  $("#profile-city").value = state.me.city || "";
  $("#profile-goals").value = state.me.buddy_goals || "";
  $("#profile-interests").value = state.me.interests || "";
  $("#me-summary").innerHTML = `
    <span class="pill">TRUST ${state.me.trust_score || 50}/100</span>
    <p>${htmlEscape(state.me.email)} · ${state.me.is_email_verified ? "verified" : "email pending"}</p>
  `;
}

async function loadPeople() {
  const query = $("#people-query").value;
  const data = await api(`/profiles/discover?q=${encodeURIComponent(query)}`);
  $("#people-list").innerHTML = data.people.map((person) => `
    <article class="person">
      <div class="row">
        <h3>${htmlEscape(person.display_name)}</h3>
        <span class="pill">${htmlEscape(person.online_status)}</span>
      </div>
      <p>${htmlEscape(person.bio || "No bio yet")}</p>
      <p class="mono">${htmlEscape(person.city || "remote")} · trust ${person.trust_score || 50}</p>
      <button class="ghost" data-request="${person.user_id}">SEND REQUEST</button>
    </article>
  `).join("");
}

async function loadRequests() {
  const data = await api("/requests");
  $("#request-list").innerHTML = data.requests.map((request) => `
    <article class="request">
      <h3>${htmlEscape(request.sender_name || `User #${request.sender_id}`)}</h3>
      <p>${htmlEscape(request.message)}</p>
      <p class="mono">${htmlEscape(request.request_type)} · ${htmlEscape(request.status)}</p>
      ${request.receiver_id === state.me.user_id && request.status === "pending" ? `
        <button class="primary" data-answer="${request.id}:accepted">ACCEPT</button>
        <button class="secondary" data-answer="${request.id}:declined">DECLINE</button>
      ` : ""}
    </article>
  `).join("");
}

async function loadChats() {
  const data = await api("/chats");
  $("#chat-list").innerHTML = data.chats.map((chat) => `
    <button class="ghost" data-chat="${chat.id}">CHAT #${chat.id}</button>
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
      <span class="mono">${htmlEscape(message.moderation_status)}</span>
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
    if (message.event.startsWith("webrtc.")) {
      await handleSignal(message);
    }
  });
}

async function sendChatMessage(event) {
  event.preventDefault();
  const body = $("#message-body").value.trim();
  if (!body || !state.currentChatId) return;
  await api(`/chats/${state.currentChatId}/messages`, {
    method: "POST",
    body: JSON.stringify({ chat_id: state.currentChatId, body }),
  });
  state.socket?.send(JSON.stringify({ event: "chat.message", chat_id: state.currentChatId, body }));
  $("#message-body").value = "";
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

function bindApp() {
  document.querySelectorAll(".sidebar a").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      setView(link.dataset.view);
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
        bio: $("#profile-bio").value,
        city: $("#profile-city").value,
        buddy_goals: $("#profile-goals").value,
        interests: $("#profile-interests").value,
      }),
    });
    await loadMe();
  });
  $("#people-list").addEventListener("click", async (event) => {
    const userId = event.target.dataset.request;
    if (!userId) return;
    await api("/requests", {
      method: "POST",
      body: JSON.stringify({ receiver_id: Number(userId), request_type: "friend", message: "Let’s connect on MFriends." }),
    });
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
  $("#message-form").addEventListener("submit", sendChatMessage);
  $("#call-start").addEventListener("click", startCall);
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
