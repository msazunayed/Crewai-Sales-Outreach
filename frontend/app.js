const $ = (s) => document.querySelector(s);
const form = $('#lead-form');
const runBtn = $('#run-btn');
const state = { profile: '', campaign: '', tab: 'profile' };

// Same origin when served by FastAPI; fall back to localhost if the file is opened directly.
const API = location.protocol.startsWith('http') && location.port === '8000' ? '' : 'http://localhost:8000';

function show(id, on) { $(id).hidden = !on; }

function renderPanel() {
  const md = state[state.tab] || '_Nothing here yet._';
  $('#panel').innerHTML = DOMPurify.sanitize(marked.parse(md));
  document.querySelectorAll('.tab').forEach((t) => {
    const active = t.dataset.tab === state.tab;
    t.classList.toggle('active', active);
    t.setAttribute('aria-selected', String(active));
  });
}

function setStage(stage) {
  const order = ['profiling', 'outreach'];
  document.querySelectorAll('#progress li').forEach((li) => {
    const i = order.indexOf(li.dataset.stage);
    const cur = stage === 'done' ? order.length : order.indexOf(stage);
    li.className = i < cur ? 'done' : i === cur ? 'active' : '';
  });
}

function fail(message) {
  const el = $('#error');
  el.textContent = message;
  show('#error', true);
  show('#progress', false);
  runBtn.disabled = false;
  runBtn.textContent = 'Run the crew';
}

async function poll(jobId) {
  try {
    const res = await fetch(`${API}/api/jobs/${jobId}`);
    const job = await res.json();
    if (!res.ok) throw new Error(job.detail || 'Request failed');
    setStage(job.stage);
    if (job.status === 'running') return setTimeout(() => poll(jobId), 2000);
    if (job.status === 'error') return fail(job.error || 'The crew failed. Check the server logs.');
    state.profile = job.profile;
    state.campaign = job.campaign;
    state.tab = 'profile';
    renderPanel();
    show('#progress', false);
    show('#results', true);
    runBtn.disabled = false;
    runBtn.textContent = 'Run the crew';
  } catch (e) {
    fail(`Lost connection to the server. ${e.message}`);
  }
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  show('#error', false);
  show('#results', false);
  show('#empty', false);
  show('#progress', true);
  setStage('profiling');
  runBtn.disabled = true;
  runBtn.textContent = 'Crew is working…';
  try {
    const res = await fetch(`${API}/api/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(Object.fromEntries(new FormData(form))),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Request failed');
    poll(data.job_id);
  } catch (err) {
    fail(err.message.includes('Failed to fetch')
      ? "Can't reach the server. Start it with: uvicorn main:app --app-dir ai --port 8000 (from the project root)."
      : err.message);
  }
});

document.querySelectorAll('.tab').forEach((t) =>
  t.addEventListener('click', () => { state.tab = t.dataset.tab; renderPanel(); }));

$('#copy-btn').addEventListener('click', async (e) => {
  await navigator.clipboard.writeText(state[state.tab]);
  e.target.textContent = 'Copied';
  setTimeout(() => (e.target.textContent = 'Copy'), 1500);
});

$('#download-btn').addEventListener('click', () => {
  const name = state.tab === 'profile' ? 'lead_profile.md' : 'outreach_campaign.md';
  const url = URL.createObjectURL(new Blob([state[state.tab]], { type: 'text/markdown' }));
  const a = Object.assign(document.createElement('a'), { href: url, download: name });
  a.click();
  URL.revokeObjectURL(url);
});

fetch(`${API}/api/health`).then((r) => r.json()).then((h) => {
  $('#health').textContent = h.llm_key && h.serper_key
    ? 'Server ready. API keys found.'
    : 'Add your API keys to .env and restart the server.';
}).catch(() => { $('#health').textContent = 'Server not reachable yet.'; });
