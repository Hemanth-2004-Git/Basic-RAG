// ── State ──────────────────────────────────────────────────────────────────
let isLoading = false;

// ── Init ───────────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  fetchStatus();
  fetchDocuments();
  setupUpload();
  setupTextarea();
});

// ── Status ─────────────────────────────────────────────────────────────────
async function fetchStatus() {
  try {
    const res  = await fetch('/api/status');
    const data = await res.json();
    document.getElementById('statusDot').classList.add('ready');
    document.getElementById('statusVal').textContent = 'Ready';
    document.getElementById('chunkCount').textContent = data.total_chunks;
  } catch {
    document.getElementById('statusVal').textContent = 'Offline';
  }
}

// ── Documents ──────────────────────────────────────────────────────────────
async function fetchDocuments() {
  try {
    const res  = await fetch('/api/documents');
    const data = await res.json();
    document.getElementById('docCount').textContent = data.count;
    const list = document.getElementById('docList');
    list.innerHTML = '';
    if (data.documents.length === 0) {
      list.innerHTML = '<li class="doc-item loading-pill">No documents yet</li>';
    } else {
      data.documents.forEach(name => {
        const li = document.createElement('li');
        li.className = 'doc-item';
        li.textContent = name;
        list.appendChild(li);
      });
    }
  } catch {
    document.getElementById('docList').innerHTML = '<li class="doc-item loading-pill">Error loading</li>';
  }
}

// ── Upload ─────────────────────────────────────────────────────────────────
function setupUpload() {
  const zone   = document.getElementById('uploadZone');
  const input  = document.getElementById('fileInput');
  const status = document.getElementById('uploadStatus');

  zone.addEventListener('click', () => input.click());

  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag'));
  zone.addEventListener('drop', e => {
    e.preventDefault(); zone.classList.remove('drag');
    if (e.dataTransfer.files[0]) uploadFile(e.dataTransfer.files[0]);
  });

  input.addEventListener('change', () => { if (input.files[0]) uploadFile(input.files[0]); });

  async function uploadFile(file) {
    status.textContent = '⏳ Uploading & indexing…';
    status.className   = 'upload-status';
    const form = new FormData();
    form.append('file', file);
    try {
      const res  = await fetch('/api/upload', { method: 'POST', body: form });
      const data = await res.json();
      if (res.ok) {
        status.textContent = `✅ ${data.message}`;
        status.className   = 'upload-status ok';
        fetchDocuments(); fetchStatus();
      } else {
        status.textContent = `❌ ${data.error}`;
        status.className   = 'upload-status err';
      }
    } catch {
      status.textContent = '❌ Upload failed';
      status.className   = 'upload-status err';
    }
    input.value = '';
  }
}

// ── Textarea auto-resize + Enter to send ──────────────────────────────────
function setupTextarea() {
  const ta = document.getElementById('queryInput');
  ta.addEventListener('input', () => {
    ta.style.height = 'auto';
    ta.style.height = ta.scrollHeight + 'px';
  });
  ta.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendQuery(); }
  });
}

// ── Prefill sample query ───────────────────────────────────────────────────
function prefill(text) {
  const ta = document.getElementById('queryInput');
  ta.value = text;
  ta.dispatchEvent(new Event('input'));
  ta.focus();
}

// ── Send query ─────────────────────────────────────────────────────────────
async function sendQuery() {
  if (isLoading) return;
  const ta       = document.getElementById('queryInput');
  const question = ta.value.trim();
  if (!question) return;

  // Hide welcome card
  const wc = document.getElementById('welcomeCard');
  if (wc) wc.remove();

  ta.value = '';
  ta.style.height = 'auto';

  appendMessage('user', question);
  const typingEl = appendTyping();
  setSending(true);

  try {
    const res  = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();
    typingEl.remove();

    if (data.error) {
      appendMessage('ai', `⚠️ ${data.error}`);
    } else {
      appendAIMessage(data);
    }
  } catch (err) {
    typingEl.remove();
    appendMessage('ai', '⚠️ Could not reach the server. Make sure app.py is running.');
  } finally {
    setSending(false);
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────
function setSending(state) {
  isLoading = state;
  const btn = document.getElementById('sendBtn');
  btn.disabled = state;
  document.getElementById('sendIcon').textContent = state ? '…' : '➤';
}

function appendMessage(role, text) {
  const wrap = document.getElementById('chatWrap');
  const msg  = document.createElement('div');
  msg.className = `msg msg-${role}`;

  const bub = document.createElement('div');
  bub.className = `bubble bubble-${role}`;
  bub.textContent = text;

  msg.appendChild(bub);
  wrap.appendChild(msg);
  wrap.scrollTop = wrap.scrollHeight;
  return msg;
}

function appendAIMessage(data) {
  const wrap = document.getElementById('chatWrap');
  const msg  = document.createElement('div');
  msg.className = 'msg msg-ai';

  // Answer bubble
  const bub = document.createElement('div');
  bub.className = 'bubble bubble-ai';
  bub.textContent = data.answer;
  msg.appendChild(bub);

  // Sources
  if (data.sources && data.sources.length) {
    const row = document.createElement('div');
    row.className = 'sources-row';
    data.sources.forEach(s => {
      const tag = document.createElement('span');
      tag.className = 'source-tag';
      tag.textContent = '📄 ' + s;
      row.appendChild(tag);
    });
    msg.appendChild(row);
  }

  // Context toggle
  if (data.context_used && data.context_used.length) {
    const toggle = document.createElement('span');
    toggle.className = 'context-toggle';
    toggle.textContent = '🔍 Show retrieved context';

    const box = document.createElement('div');
    box.className = 'context-box';

    data.context_used.forEach((c, i) => {
      const p = document.createElement('p');
      p.style.marginBottom = '8px';
      p.innerHTML = `<b>[${i+1}] ${c.source}</b> (score: ${c.score.toFixed(3)})<br>${c.text}`;
      box.appendChild(p);
    });

    toggle.addEventListener('click', () => {
      box.classList.toggle('open');
      toggle.textContent = box.classList.contains('open')
        ? '🔍 Hide retrieved context'
        : '🔍 Show retrieved context';
    });

    msg.appendChild(toggle);
    msg.appendChild(box);
  }

  wrap.appendChild(msg);
  wrap.scrollTop = wrap.scrollHeight;
}

function appendTyping() {
  const wrap = document.getElementById('chatWrap');
  const msg  = document.createElement('div');
  msg.className = 'msg msg-ai';

  const bub = document.createElement('div');
  bub.className = 'bubble bubble-ai typing';
  bub.innerHTML = '<span></span><span></span><span></span>';

  msg.appendChild(bub);
  wrap.appendChild(msg);
  wrap.scrollTop = wrap.scrollHeight;
  return msg;
}
