/**
 * Chat panel controller.
 * Talks to POST /api/chat/message and GET /api/chat/history.
 * Session is a random ID kept in localStorage so a page reload
 * restores the same conversation.
 */

// Namespaced per logged-in user (or "guest") so switching accounts
// on the same browser starts a fresh conversation instead of
// continuing the previous person's chat history.
const SESSION_KEY = "ai_news_chat_session_id_" + (window.CURRENT_USER_ID || "guest");

document.addEventListener("DOMContentLoaded", () => {
  const fab = document.getElementById("aiChatFab");
  const panel = document.getElementById("chatPanel");
  const closeBtn = document.getElementById("chatPanelClose");
  const navLink = document.getElementById("navChatLink");
  const form = document.getElementById("chatPanelForm");
  const input = document.getElementById("chatPanelInput");

  if (!fab || !panel || !form) return;

  const sessionId = getOrCreateSessionId();
  restoreHistory(sessionId);

  fab.addEventListener("click", () => togglePanel(true));
  closeBtn.addEventListener("click", () => togglePanel(false));

  // Clicking the hero preview card's send button opens the real chat
  // panel — the preview itself is just a static illustration.
  const heroChatBtn = document.getElementById("heroChatPreviewBtn");
  if (heroChatBtn) {
    heroChatBtn.addEventListener("click", (e) => {
      e.preventDefault();
      togglePanel(true);
    });
  }
  if (navLink) {
    navLink.addEventListener("click", (e) => {
      e.preventDefault();
      togglePanel(true);
    });
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    sendMessage(sessionId, message);
  });

  function togglePanel(open) {
    panel.classList.toggle("open", open);
    if (open) input.focus();
  }
});

function getOrCreateSessionId() {
  let id = localStorage.getItem(SESSION_KEY);
  if (!id) {
    id = "sess-" + Date.now() + "-" + Math.random().toString(36).slice(2, 10);
    localStorage.setItem(SESSION_KEY, id);
  }
  return id;
}

async function restoreHistory(sessionId) {
  try {
    const resp = await fetch(`/api/chat/history?session_id=${encodeURIComponent(sessionId)}`);
    const data = await resp.json();
    if (!data.ok || !data.messages.length) return;

    const body = document.getElementById("chatPanelBody");
    body.innerHTML = "";
    data.messages.forEach((m) => appendMessage(m.role, m.message));
  } catch (err) {
    // Ignore — worst case the default greeting stays.
  }
}

async function sendMessage(sessionId, message) {
  appendMessage("user", message);
  setTyping(true);

  try {
    const resp = await fetch("/api/chat/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
    });
    const data = await resp.json();

    setTyping(false);

    if (!data.ok) {
      appendMessage("bot", data.error || "Something went wrong. Please try again.", { isError: true });
      return;
    }

    appendMessage("bot", data.reply, { sources: data.sources });
  } catch (err) {
    setTyping(false);
    appendMessage("bot", "Network error — check your connection and try again.", { isError: true });
  }
}

function appendMessage(role, text, { sources = [], isError = false } = {}) {
  const body = document.getElementById("chatPanelBody");
  const bubble = document.createElement("div");
  bubble.className = `msg ${role === "user" ? "msg-user" : "msg-bot"}`;
  if (isError) bubble.style.borderColor = "#dc3545";

  const textEl = document.createElement("div");
  textEl.textContent = text;
  bubble.appendChild(textEl);

  if (sources && sources.length) {
    const sourcesEl = document.createElement("div");
    sourcesEl.className = "msg-sources";
    sourcesEl.innerHTML =
      "<strong>Sources:</strong><br>" +
      sources.map((s) => `<a href="${s.url}" target="_blank" rel="noopener">${escapeHtml(s.source)}: ${escapeHtml(s.title)}</a>`).join("<br>");
    bubble.appendChild(sourcesEl);
  }

  const timeEl = document.createElement("span");
  timeEl.className = "msg-timestamp";
  timeEl.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  bubble.appendChild(timeEl);

  body.appendChild(bubble);
  body.scrollTop = body.scrollHeight;
}

function setTyping(show) {
  const el = document.getElementById("chatTypingIndicator");
  if (el) el.classList.toggle("d-none", !show);
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}