/**
 * TaskFlow — Groq AI Floating Chat Assistant
 */

let aiChatHistory = [];
let isWaitingForAI = false;

function toggleAIChat() {
  const panel = document.getElementById('aiChatPanel');
  if (panel) {
    panel.classList.toggle('open');
    if (panel.classList.contains('open')) {
      const input = document.getElementById('aiMessageInput');
      if (input) input.focus();
      scrollAIChatToBottom();
    }
  }
}

function handleAIChatKey(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendAIMessage();
  }
}

function scrollAIChatToBottom() {
  const container = document.getElementById('aiMessages');
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
}

function appendUserMessage(text) {
  const container = document.getElementById('aiMessages');
  const msgDiv = document.createElement('div');
  msgDiv.className = 'ai-msg user-msg';
  msgDiv.innerHTML = `
    <div class="ai-msg-bubble">${escapeHtml(text)}</div>
  `;
  container.appendChild(msgDiv);
  scrollAIChatToBottom();
}

function appendAssistantMessage(text) {
  const container = document.getElementById('aiMessages');
  const msgDiv = document.createElement('div');
  msgDiv.className = 'ai-msg assistant-msg';
  msgDiv.innerHTML = `
    <div class="ai-msg-avatar"><i class="bi bi-stars"></i></div>
    <div class="ai-msg-bubble">${formatAIMessage(text)}</div>
  `;
  container.appendChild(msgDiv);
  scrollAIChatToBottom();
}

function showTypingIndicator() {
  const container = document.getElementById('aiMessages');
  const typingDiv = document.createElement('div');
  typingDiv.className = 'ai-msg assistant-msg';
  typingDiv.id = 'aiTypingIndicator';
  typingDiv.innerHTML = `
    <div class="ai-msg-avatar"><i class="bi bi-stars"></i></div>
    <div class="ai-typing">
      <span></span><span></span><span></span>
    </div>
  `;
  container.appendChild(typingDiv);
  scrollAIChatToBottom();
}

function removeTypingIndicator() {
  const elem = document.getElementById('aiTypingIndicator');
  if (elem) elem.remove();
}

function sendAIMessage() {
  if (isWaitingForAI) return;

  const input = document.getElementById('aiMessageInput');
  const message = input.value.trim();

  if (!message) return;

  // Clear input
  input.value = '';

  // Render user message
  appendUserMessage(message);

  // Show typing state
  isWaitingForAI = true;
  showTypingIndicator();

  const sendBtn = document.getElementById('aiSendBtn');
  if (sendBtn) sendBtn.disabled = true;

  fetch('/assistant/chat/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: JSON.stringify({
      message: message,
      history: aiChatHistory
    })
  })
  .then(res => res.json())
  .then(data => {
    removeTypingIndicator();
    isWaitingForAI = false;
    if (sendBtn) sendBtn.disabled = false;

    if (data.success && data.response) {
      appendAssistantMessage(data.response);
      // Track history (keep last 8 interactions)
      aiChatHistory.push({ role: 'user', content: message });
      aiChatHistory.push({ role: 'assistant', content: data.response });
      if (aiChatHistory.length > 8) {
        aiChatHistory = aiChatHistory.slice(-8);
      }
    } else {
      appendAssistantMessage(data.error || 'Sorry, I encountered an issue processing your request.');
    }
  })
  .catch(err => {
    console.error('Chat error:', err);
    removeTypingIndicator();
    isWaitingForAI = false;
    if (sendBtn) sendBtn.disabled = false;
    appendAssistantMessage('Unable to reach the AI assistant. Please check your network or API key configuration.');
  });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.innerText = text;
  return div.innerHTML;
}

function formatAIMessage(text) {
  // Convert newlines to breaks and escape dangerous HTML
  let formatted = escapeHtml(text).replace(/\n/g, '<br>');
  // Format simple bullet points if any
  formatted = formatted.replace(/•\s*(.*?)(<br>|$)/g, '<li>$1</li>');
  if (formatted.includes('<li>')) {
    formatted = '<ul style="padding-left:18px;margin:4px 0;">' + formatted + '</ul>';
  }
  return formatted;
}

