// ── File Upload ──────────────────────────────────────────────
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileList  = document.getElementById('file-list');

dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  uploadFiles(e.dataTransfer.files);
});
fileInput.addEventListener('change', () => uploadFiles(fileInput.files));

async function uploadFiles(files) {
  const formData = new FormData();
  for (const file of files) formData.append('files', file);

  const res  = await fetch('/upload', { method: 'POST', body: formData });
  const data = await res.json();

  data.uploaded.forEach(name => {
    const tag = document.createElement('span');
    tag.className = 'file-tag';
    tag.textContent = name;
    fileList.appendChild(tag);
  });
}

// ── Fetch JD ─────────────────────────────────────────────────
async function fetchJD() {
  const url     = document.getElementById('job-url').value.trim();
  const warning = document.getElementById('fetch-warning');
  const btn     = document.getElementById('fetch-btn');

  if (!url) return;

  btn.disabled = true;
  btn.textContent = 'Fetching...';
  warning.classList.add('hidden');

  const res  = await fetch('/fetch-jd', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url })
  });
  const data = await res.json();

  btn.disabled = false;
  btn.textContent = 'Fetch';

  if (data.error) {
    warning.textContent = data.error;
    warning.classList.remove('hidden');
    return;
  }

  if (data.warning) {
    warning.textContent = data.warning;
    warning.classList.remove('hidden');
  }

  if (data.text && data.text.length > 50) {
    document.getElementById('job-description').value = data.text;
  }
}

// ── Run Agent ─────────────────────────────────────────────────
async function runAgent() {
  const jd  = document.getElementById('job-description').value.trim();
  const btn = document.getElementById('run-btn');

  if (!jd || jd.length < 50) {
    alert('Please add a job description first.');
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Running...';

  // Show progress
  show('progress-section');
  hide('match-section');
  hide('result-section');
  hide('error-section');

  const res  = await fetch('/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_description: jd })
  });
  const data = await res.json();

  if (data.error) {
    showError(data.error);
    btn.disabled = false;
    btn.textContent = 'Analyse & Build Resume';
    return;
  }

  pollStatus(data.job_id, btn);
}

const PROGRESS_MAP = {
  starting:      5,
  loading_docs:  15,
  matching:      30,
  waiting:       50,
  building:      70,
  generating:    90,
  done:          100,
  error:         100,
};

function pollStatus(jobId, btn) {
  const interval = setInterval(async () => {
    const res  = await fetch(`/status/${jobId}`);
    const data = await res.json();

    setProgress(PROGRESS_MAP[data.status] || 0, data.message);

    if (data.status === 'done') {
      clearInterval(interval);
      btn.disabled = false;
      btn.textContent = 'Analyse & Build Resume';
      showMatch(data.match);
      showResult(data);
    }

    if (data.status === 'error') {
      clearInterval(interval);
      btn.disabled = false;
      btn.textContent = 'Analyse & Build Resume';
      showError(data.message);
    }
  }, 2000);
}

function setProgress(pct, msg) {
  document.getElementById('progress-bar').style.width = pct + '%';
  document.getElementById('progress-message').textContent = msg;
}

function showMatch(match) {
  if (!match) return;
  show('match-section');

  const pct   = match.match_pct || 0;
  const emoji = pct >= 70 ? '✅' : pct >= 50 ? '👍' : pct >= 30 ? '⚠️' : '❌';
  document.getElementById('match-score').textContent =
    `${emoji}  ${pct}% Match  —  ${match.rating || ''}`;

  const strengthsList = document.getElementById('strengths-list');
  strengthsList.innerHTML = '';
  (match.strengths || []).forEach(s => {
    const li = document.createElement('li');
    li.textContent = s;
    strengthsList.appendChild(li);
  });

  const gapsList = document.getElementById('gaps-list');
  gapsList.innerHTML = '';
  (match.gaps || []).forEach(g => {
    const li = document.createElement('li');
    li.textContent = g;
    gapsList.appendChild(li);
  });

  const kwDiv = document.getElementById('missing-kw');
  kwDiv.innerHTML = '';
  (match.missing_keywords || []).slice(0, 20).forEach(kw => {
    const tag = document.createElement('span');
    tag.className = 'kw-tag';
    tag.textContent = kw;
    kwDiv.appendChild(tag);
  });
}

function showResult(data) {
  show('result-section');
  document.getElementById('ats-badge').textContent =
    `Estimated ATS Score: ${data.ats_score}/100`;

  const list = document.getElementById('suggestions-list');
  list.innerHTML = '';
  (data.suggestions || []).forEach(s => {
    const li = document.createElement('li');
    li.textContent = s;
    list.appendChild(li);
  });

  const dlBtn = document.getElementById('download-btn');
  dlBtn.href = `/download/${encodeURIComponent(data.filename)}`;
  dlBtn.textContent = `Download ${data.filename}`;
}

function showError(msg) {
  show('error-section');
  document.getElementById('error-message').textContent = msg;
  hide('progress-section');
}

function reset() {
  hide('error-section');
  hide('progress-section');
  hide('match-section');
  hide('result-section');
}

function show(id) { document.getElementById(id).classList.remove('hidden'); }
function hide(id) { document.getElementById(id).classList.add('hidden'); }
