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
  if (!text) return '';

  // Extract code blocks first to protect code content from text replacements
  const codeBlocks = [];
  let processed = text.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, function(match, lang, code) {
    const placeholder = `__CODE_BLOCK_${codeBlocks.length}__`;
    codeBlocks.push({ lang: (lang || '').trim(), code: escapeHtml(code.trim()) });
    return placeholder;
  });

  // Extract inline code
  const inlineCodes = [];
  processed = processed.replace(/`([^`\n]+)`/g, function(match, code) {
    const placeholder = `__INLINE_CODE_${inlineCodes.length}__`;
    inlineCodes.push(escapeHtml(code));
    return placeholder;
  });

  // Escape HTML in the rest of the text
  processed = escapeHtml(processed);

  // Restore inline codes
  inlineCodes.forEach((code, idx) => {
    processed = processed.replace(`__INLINE_CODE_${idx}__`, `<code>${code}</code>`);
  });

  // Split into lines for block-level processing
  const lines = processed.split('\n');
  const outputLines = [];
  let inUl = false;
  let inOl = false;

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i].trim();

    // Check code block placeholder
    if (line.startsWith('__CODE_BLOCK_') && line.endsWith('__')) {
      if (inUl) { outputLines.push('</ul>'); inUl = false; }
      if (inOl) { outputLines.push('</ol>'); inOl = false; }
      const blockIdx = parseInt(line.replace('__CODE_BLOCK_', '').replace('__', ''), 10);
      const block = codeBlocks[blockIdx];
      if (block) {
        outputLines.push(`<pre><code class="language-${block.lang}">${block.code}</code></pre>`);
      }
      continue;
    }

    // Horizontal Rule
    if (/^(\-{3,}|\*{3,}|_{3,})$/.test(line)) {
      if (inUl) { outputLines.push('</ul>'); inUl = false; }
      if (inOl) { outputLines.push('</ol>'); inOl = false; }
      outputLines.push('<hr>');
      continue;
    }

    // Headings (###, ##, #)
    const h3Match = line.match(/^###\s+(.+)$/);
    if (h3Match) {
      if (inUl) { outputLines.push('</ul>'); inUl = false; }
      if (inOl) { outputLines.push('</ol>'); inOl = false; }
      outputLines.push(`<h3>${formatInlineStyles(h3Match[1])}</h3>`);
      continue;
    }

    const h2Match = line.match(/^##\s+(.+)$/);
    if (h2Match) {
      if (inUl) { outputLines.push('</ul>'); inUl = false; }
      if (inOl) { outputLines.push('</ol>'); inOl = false; }
      outputLines.push(`<h2>${formatInlineStyles(h2Match[1])}</h2>`);
      continue;
    }

    const h1Match = line.match(/^#\s+(.+)$/);
    if (h1Match) {
      if (inUl) { outputLines.push('</ul>'); inUl = false; }
      if (inOl) { outputLines.push('</ol>'); inOl = false; }
      outputLines.push(`<h1>${formatInlineStyles(h1Match[1])}</h1>`);
      continue;
    }

    // Blockquote
    const bqMatch = line.match(/^>\s+(.+)$/);
    if (bqMatch) {
      if (inUl) { outputLines.push('</ul>'); inUl = false; }
      if (inOl) { outputLines.push('</ol>'); inOl = false; }
      outputLines.push(`<blockquote>${formatInlineStyles(bqMatch[1])}</blockquote>`);
      continue;
    }

    // Checklists (- [ ] or - [x])
    const checkMatch = line.match(/^[-*•]\s+\[([ xX])\]\s+(.+)$/);
    if (checkMatch) {
      if (inOl) { outputLines.push('</ol>'); inOl = false; }
      if (!inUl) { outputLines.push('<ul>'); inUl = true; }
      const checked = checkMatch[1].toLowerCase() === 'x' ? 'checked' : '';
      outputLines.push(`<li style="list-style:none;margin-left:-14px;"><input type="checkbox" ${checked} disabled style="margin-right:6px;vertical-align:middle;">${formatInlineStyles(checkMatch[2])}</li>`);
      continue;
    }

    // Unordered List (- , * , • )
    const ulMatch = line.match(/^[-*•]\s+(.+)$/);
    if (ulMatch) {
      if (inOl) { outputLines.push('</ol>'); inOl = false; }
      if (!inUl) { outputLines.push('<ul>'); inUl = true; }
      outputLines.push(`<li>${formatInlineStyles(ulMatch[1])}</li>`);
      continue;
    }

    // Ordered List (1. , 2. )
    const olMatch = line.match(/^(\d+)\.\s+(.+)$/);
    if (olMatch) {
      if (inUl) { outputLines.push('</ul>'); inUl = false; }
      if (!inOl) { outputLines.push('<ol>'); inOl = true; }
      outputLines.push(`<li>${formatInlineStyles(olMatch[2])}</li>`);
      continue;
    }

    // Regular line / Paragraph
    if (inUl) { outputLines.push('</ul>'); inUl = false; }
    if (inOl) { outputLines.push('</ol>'); inOl = false; }

    if (!line) {
      outputLines.push('');
    } else {
      outputLines.push(`<p>${formatInlineStyles(line)}</p>`);
    }
  }

  if (inUl) outputLines.push('</ul>');
  if (inOl) outputLines.push('</ol>');

  return outputLines.filter(l => l !== '').join('\n');
}

function formatInlineStyles(str) {
  if (!str) return '';
  // Bold (**text** or __text__)
  let s = str.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/__(.+?)__/g, '<strong>$1</strong>');
  // Italic (*text* or _text_)
  s = s.replace(/\*([^\*\n]+?)\*/g, '<em>$1</em>');
  s = s.replace(/_([^_\n]+?)_/g, '<em>$1</em>');
  return s;
}

