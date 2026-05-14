"use strict";

// ------------------------------------------------------------------
// DOM refs
// ------------------------------------------------------------------
const urlInput       = document.getElementById("url-input");
const processBtn     = document.getElementById("process-btn");
const processBtnText = document.getElementById("process-btn-text");
const processIcon    = document.getElementById("process-icon");
const statusBar      = document.getElementById("status-bar");
const statusMessage  = document.getElementById("status-message");
const progressSec    = document.getElementById("progress-section");
const progressDetail = document.getElementById("progress-detail");
const embedSec       = document.getElementById("embed-section");
const ytEmbed        = document.getElementById("yt-embed");
const messagesEl     = document.getElementById("messages");
const questionInput  = document.getElementById("question-input");
const askBtn         = document.getElementById("ask-btn");
const chatSubtitle   = document.getElementById("chat-subtitle");
const clearBtn       = document.getElementById("clear-btn");

// ------------------------------------------------------------------
// State
// ------------------------------------------------------------------
let pollTimer = null;

// ------------------------------------------------------------------
// Init: check current server state on page load
// ------------------------------------------------------------------
(async () => {
  try {
    const data = await apiFetch("/api/status");
    applyServerState(data);
    if (data.status === "processing") startPolling();
  } catch {
    setStatus("error", "Cannot reach server — is the API running?");
  }
})();

// ------------------------------------------------------------------
// Event listeners
// ------------------------------------------------------------------
processBtn.addEventListener("click", handleProcess);
urlInput.addEventListener("keydown", (e) => { if (e.key === "Enter") handleProcess(); });

questionInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleAsk(); }
});
askBtn.addEventListener("click", handleAsk);
clearBtn.addEventListener("click", clearChat);

// ------------------------------------------------------------------
// Process video
// ------------------------------------------------------------------
async function handleProcess() {
  const url = urlInput.value.trim();
  if (!url) { urlInput.focus(); return; }

  setProcessingUI(true);
  hideEmbed();

  try {
    const data = await apiFetch("/api/process", {
      method: "POST",
      body: JSON.stringify({ url }),
    });

    if (data.detail) {
      // Error response
      setStatus("error", data.detail);
      setProcessingUI(false);
      return;
    }

    startPolling();
  } catch (err) {
    setStatus("error", "Failed to reach the server.");
    setProcessingUI(false);
  }
}

// ------------------------------------------------------------------
// Polling
// ------------------------------------------------------------------
function startPolling() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    try {
      const data = await apiFetch("/api/status");
      applyServerState(data);
      if (data.status !== "processing") {
        clearInterval(pollTimer);
        pollTimer = null;
        setProcessingUI(false);
      }
    } catch {
      // network blip — keep polling
    }
  }, 2000);
}

// ------------------------------------------------------------------
// Apply status from server
// ------------------------------------------------------------------
function applyServerState({ status, message, video_url, error }) {
  setStatus(status, message || error || "");

  if (status === "processing") {
    progressSec.classList.remove("hidden");
    progressDetail.textContent = message;
    disableChat();
  } else if (status === "ready") {
    progressSec.classList.add("hidden");
    enableChat(video_url);
    if (video_url) showEmbed(video_url);
  } else {
    progressSec.classList.add("hidden");
  }
}

// ------------------------------------------------------------------
// Status bar helpers
// ------------------------------------------------------------------
function setStatus(status, msg) {
  statusBar.className = `status-bar status-${status}`;
  statusMessage.textContent = msg;
}

// ------------------------------------------------------------------
// Chat state helpers
// ------------------------------------------------------------------
function enableChat(videoUrl) {
  questionInput.disabled = false;
  askBtn.disabled = false;
  chatSubtitle.textContent = "Ask anything about the video";

  // Clear welcome card on first ready
  if (messagesEl.querySelector(".welcome-card")) {
    messagesEl.innerHTML = "";
  }
}

function disableChat() {
  questionInput.disabled = true;
  askBtn.disabled = true;
}

function clearChat() {
  messagesEl.innerHTML = "";
}

// ------------------------------------------------------------------
// Processing UI helpers
// ------------------------------------------------------------------
function setProcessingUI(on) {
  processBtn.disabled    = on;
  urlInput.disabled      = on;
  processBtnText.textContent = on ? "Processing…" : "Process Video";
  processIcon.style.opacity  = on ? "0.5" : "1";
}

// ------------------------------------------------------------------
// Video embed
// ------------------------------------------------------------------
function showEmbed(url) {
  const id = extractVideoId(url);
  if (!id) return;
  ytEmbed.src = `https://www.youtube.com/embed/${id}`;
  embedSec.classList.remove("hidden");
}

function hideEmbed() {
  ytEmbed.src = "";
  embedSec.classList.add("hidden");
}

function extractVideoId(url) {
  try {
    const u = new URL(url);
    if (u.hostname === "youtu.be") return u.pathname.slice(1).split("?")[0];
    if (u.hostname.includes("youtube.com")) return u.searchParams.get("v");
  } catch {
    // not a valid URL
  }
  return null;
}

// ------------------------------------------------------------------
// Ask question
// ------------------------------------------------------------------
async function handleAsk() {
  const question = questionInput.value.trim();
  if (!question || askBtn.disabled) return;

  questionInput.value = "";
  setAskingUI(true);

  appendUserMessage(question);
  const thinkingEl = appendThinking();

  try {
    const data = await apiFetch("/api/ask", {
      method: "POST",
      body: JSON.stringify({ question }),
    });
    thinkingEl.remove();

    if (data.detail) {
      appendBotMessage(`Error: ${data.detail}`, []);
    } else {
      appendBotMessage(data.answer, data.sources || []);
    }
  } catch {
    thinkingEl.remove();
    appendBotMessage("Could not reach the server. Please try again.", []);
  } finally {
    setAskingUI(false);
    questionInput.focus();
  }
}

function setAskingUI(on) {
  askBtn.disabled         = on;
  questionInput.disabled  = on;
}

// ------------------------------------------------------------------
// Message rendering
// ------------------------------------------------------------------
function appendUserMessage(text) {
  const row = document.createElement("div");
  row.className = "message user";

  const avatar = makeAvatar("👤");
  const body   = document.createElement("div");
  body.className = "msg-body";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  body.appendChild(bubble);
  row.appendChild(avatar);
  row.appendChild(body);
  messagesEl.appendChild(row);
  scrollToBottom();
}

function appendBotMessage(text, sources) {
  const row = document.createElement("div");
  row.className = "message bot";

  const avatar = makeAvatar("🤖");
  const body   = document.createElement("div");
  body.className = "msg-body";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  body.appendChild(bubble);

  if (sources.length > 0) {
    const sourcesRow = document.createElement("div");
    sourcesRow.className = "sources-row";

    sources.forEach(({ timestamp, preview }) => {
      const chip = document.createElement("div");
      chip.className = "source-chip";
      chip.title = preview;

      const tsSpan = document.createElement("span");
      tsSpan.className = "chip-ts";
      tsSpan.textContent = `⏱ ${timestamp}`;

      const previewSpan = document.createElement("span");
      previewSpan.className = "chip-preview";
      previewSpan.textContent = preview.slice(0, 55) + (preview.length > 55 ? "…" : "");

      chip.appendChild(tsSpan);
      chip.appendChild(previewSpan);
      sourcesRow.appendChild(chip);
    });

    body.appendChild(sourcesRow);
  }

  row.appendChild(avatar);
  row.appendChild(body);
  messagesEl.appendChild(row);
  scrollToBottom();
}

function appendThinking() {
  const row = document.createElement("div");
  row.className = "thinking-row";

  const avatar = makeAvatar("🤖");
  const bubble = document.createElement("div");
  bubble.className = "thinking-bubble";
  bubble.innerHTML = "<span></span><span></span><span></span>";

  row.appendChild(avatar);
  row.appendChild(bubble);
  messagesEl.appendChild(row);
  scrollToBottom();
  return row;
}

function makeAvatar(emoji) {
  const el = document.createElement("div");
  el.className = "msg-avatar";
  el.textContent = emoji;
  return el;
}

// ------------------------------------------------------------------
// Utilities
// ------------------------------------------------------------------
function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function apiFetch(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  return res.json();
}
