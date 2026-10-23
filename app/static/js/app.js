"use strict";

const form = document.querySelector("#chat-form");
const input = document.querySelector("#question");
const sendButton = document.querySelector("#send-button");
const messagesElement = document.querySelector("#messages");
const conversationElement = document.querySelector("#conversation");
const welcomeElement = document.querySelector("#welcome");
const toastElement = document.querySelector("#toast");
const sidebar = document.querySelector("#sidebar");
const history = [];
let isSending = false;
let toastTimer;

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

function renderMarkdown(text) {
  const safe = escapeHtml(text);
  const codeBlocks = [];
  let html = safe.replace(/```([^\n]*)\n?([\s\S]*?)```/g, (_, language, code) => {
    const block = `<pre><code>${code.trimEnd()}</code></pre>`;
    codeBlocks.push(block);
    return `\u0000${codeBlocks.length - 1}\u0000`;
  });
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>");
  html = html.split(/\n{2,}/).map((part) => {
    if (/^<(h2|h3|pre)\b/.test(part) || /^\u0000\d+\u0000$/.test(part)) return part;
    return `<p>${part.replace(/\n/g, "<br>")}</p>`;
  }).join("");
  return html.replace(/\u0000(\d+)\u0000/g, (_, index) => codeBlocks[Number(index)]);
}

function scrollToBottom() {
  conversationElement.scrollTop = conversationElement.scrollHeight;
}

function addMessage(role, content) {
  const item = document.createElement("article");
  item.className = `message ${role}`;
  const body = document.createElement("div");
  body.className = "message-body";
  if (role === "user") {
    body.textContent = content;
    item.append(body);
  } else {
    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.innerHTML = '<svg viewBox="0 0 24 24" fill="none"><path d="m12 2 2.4 7.6L22 12l-7.6 2.4L12 22l-2.4-7.6L2 12l7.6-2.4L12 2Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>';
    body.innerHTML = renderMarkdown(content);
    item.append(avatar, body);
  }
  messagesElement.append(item);
  scrollToBottom();
  return item;
}

function showToast(message) {
  toastElement.textContent = message;
  toastElement.classList.add("visible");
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toastElement.classList.remove("visible"), 3200);
}

function setSending(value) {
  isSending = value;
  input.disabled = value;
  sendButton.disabled = value || !input.value.trim();
  sendButton.setAttribute("aria-label", value ? "Sending message" : "Send message");
}

async function sendQuestion(question) {
  if (isSending || !question.trim()) return;
  welcomeElement.hidden = true;
  addMessage("user", question);
  input.value = "";
  input.style.height = "auto";
  setSending(true);
  const loading = document.createElement("article");
  loading.className = "message assistant";
  loading.setAttribute("aria-label", "Clarity is thinking");
  loading.innerHTML = '<div class="message-avatar" aria-hidden="true">✧</div><div class="typing-dots"><span></span><span></span><span></span></div>';
  messagesElement.append(loading);
  scrollToBottom();

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, history }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Something went wrong. Please try again.");
    if (typeof data.answer !== "string" || !data.answer.trim()) {
      throw new Error("The AI returned an empty answer. Please try again.");
    }
    history.push({ role: "user", content: question }, { role: "assistant", content: data.answer });
    if (history.length > 40) history.splice(0, history.length - 40);
    loading.remove();
    addMessage("assistant", data.answer);
  } catch (error) {
    loading.remove();
    addMessage("assistant", `I couldn’t answer that just now. ${error.message}`);
    showToast(error.message);
  } finally {
    setSending(false);
    input.focus();
    scrollToBottom();
  }
}

function startNewChat() {
  if (isSending) return;
  history.length = 0;
  messagesElement.replaceChildren();
  welcomeElement.hidden = false;
  input.value = "";
  input.style.height = "auto";
  sendButton.disabled = true;
  sidebar.classList.remove("open");
  input.focus();
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  sendQuestion(input.value.trim());
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
  sendButton.disabled = isSending || !input.value.trim();
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.prompt;
    sendButton.disabled = false;
    sendQuestion(input.value);
  });
});
document.querySelector("#new-chat").addEventListener("click", startNewChat);
document.querySelector("#top-new-chat").addEventListener("click", startNewChat);
document.querySelector("#mobile-menu").addEventListener("click", () => sidebar.classList.toggle("open"));
document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    startNewChat();
  }
  if (event.key === "Escape") sidebar.classList.remove("open");
});
