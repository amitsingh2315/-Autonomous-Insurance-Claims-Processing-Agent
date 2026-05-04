/* ═══════════════════════════════════════════════════════════════════════════
   Insurance Claims Processing Agent — Frontend JS
   ═══════════════════════════════════════════════════════════════════════════ */

// Determine API URL based on environment
const API_BASE = window.location.origin;

// ── DOM refs ─────────────────────────────────────────────────────────────
const uploadCard    = document.getElementById('upload-card');
const fileInput     = document.getElementById('file-input');
const btnBrowse     = document.getElementById('btn-browse');
const fileChip      = document.getElementById('file-chip');
const chipName      = document.getElementById('chip-name');
const removeFile    = document.getElementById('remove-file');
const btnProcess    = document.getElementById('btn-process');
const progressSec   = document.getElementById('progress-section');
const resultsDiv    = document.getElementById('results');
const jsonToggle    = document.getElementById('json-toggle');
const jsonBox       = document.getElementById('json-box');
const jsonPre       = document.getElementById('json-pre');
const btnReset      = document.getElementById('btn-reset');

let selectedFile = null;

// ── Step definitions ──────────────────────────────────────────────────────
const STEPS = [
  { id: 'step-extract-text',    label: 'Text Extraction',    desc: 'Reading PDF with pdfplumber',        badge: 'Automation', type: 'auto' },
  { id: 'step-extract-fields',  label: 'Field Extraction',   desc: 'Groq LLM parsing FNOL fields',       badge: 'Groq LLM',   type: 'llm'  },
  { id: 'step-validate-fields', label: 'Validation',         desc: 'Checking mandatory fields',           badge: 'Automation', type: 'auto' },
  { id: 'step-route-claim',     label: 'Claim Routing',      desc: 'Applying deterministic rules',        badge: 'Automation', type: 'auto' },
  { id: 'step-assign-claim',    label: 'Assignment',         desc: 'Intelligent claim routing',           badge: 'Automation', type: 'auto' },
  { id: 'step-reasoning',       label: 'Reasoning',          desc: 'Groq LLM generating explanation',     badge: 'Groq LLM',   type: 'llm'  },
];

// ── File selection ────────────────────────────────────────────────────────
btnBrowse.addEventListener('click', e => { e.stopPropagation(); fileInput.click(); });
uploadCard.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => { if (fileInput.files[0]) setFile(fileInput.files[0]); });

removeFile.addEventListener('click', e => { e.stopPropagation(); clearFile(); });

// ── Drag & drop ───────────────────────────────────────────────────────────
uploadCard.addEventListener('dragover',  e => { e.preventDefault(); uploadCard.classList.add('drag-over'); });
uploadCard.addEventListener('dragleave', () => uploadCard.classList.remove('drag-over'));
uploadCard.addEventListener('drop', e => {
  e.preventDefault();
  uploadCard.classList.remove('drag-over');
  const f = e.dataTransfer.files[0];
  if (f && f.type === 'application/pdf') setFile(f);
  else showToast('Please drop a PDF file.', 'error');
});

function setFile(f) {
  selectedFile = f;
  chipName.textContent = f.name;
  fileChip.classList.add('show');
  btnProcess.classList.add('show');
  resultsDiv.classList.remove('show');
  progressSec.classList.remove('show');
}

function clearFile() {
  selectedFile = null;
  fileInput.value = '';
  fileChip.classList.remove('show');
  btnProcess.classList.remove('show');
}

// ── Process ───────────────────────────────────────────────────────────────
btnProcess.addEventListener('click', async () => {
  if (!selectedFile) return;
  await runPipeline(selectedFile);
});

async function runPipeline(file) {
  // Reset UI
  resultsDiv.classList.remove('show');
  showProgress(true);
  setAllSteps('idle');
  btnProcess.disabled = true;
  btnProcess.innerHTML = '<span class="spinner"></span> Processing…';

  // Animate steps sequentially while we wait
  let stepIdx = 0;
  const stepTimer = setInterval(() => {
    if (stepIdx < STEPS.length) {
      if (stepIdx > 0) setStep(STEPS[stepIdx - 1].id, 'done');
      setStep(STEPS[stepIdx].id, 'active');
      stepIdx++;
    }
  }, 700);

  try {
    const form = new FormData();
    form.append('file', file);

    const res = await fetch(`${API_BASE}/process`, { method: 'POST', body: form });

    clearInterval(stepTimer);

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Server error');
    }

    // Mark remaining steps done
    STEPS.forEach(s => setStep(s.id, 'done'));

    const data = await res.json();
    renderResults(data);

  } catch (err) {
    clearInterval(stepTimer);
    // Mark last active step as error
    const activeEl = document.querySelector('.step.active');
    if (activeEl) activeEl.className = activeEl.className.replace('active', 'error');
    showToast(`Error: ${err.message}`, 'error');
  } finally {
    btnProcess.disabled = false;
    btnProcess.innerHTML = '&#9654; Process Claim';
  }
}

// ── Step helpers ──────────────────────────────────────────────────────────
function showProgress(show) {
  progressSec.classList.toggle('show', show);
}

function setAllSteps(state) {
  STEPS.forEach(s => setStep(s.id, state));
}

function setStep(id, state) {
  const el = document.getElementById(id);
  if (!el) return;
  el.className = 'step' + (state !== 'idle' ? ' ' + state : '');

  const icon = el.querySelector('.step-icon');
  if (state === 'done')   icon.innerHTML = '✓';
  else if (state === 'active') icon.innerHTML = '◌';
  else if (state === 'error')  icon.innerHTML = '✕';
  else icon.innerHTML = el.dataset.num;
}

// ── Render results ────────────────────────────────────────────────────────
function renderResults(data) {
  const { extractedFields: ef, missingFields, recommendedRoute, assignedTo, decisionBreakdown, confidenceScore, fraudScore, reasoning } = data;

  // Route banner
  const routeEl    = document.getElementById('route-name');
  const scoreEl    = document.getElementById('score-val');
  const bannerEl   = document.getElementById('route-banner');
  routeEl.textContent = recommendedRoute;
  scoreEl.textContent = (confidenceScore * 100).toFixed(0) + '%';
  bannerEl.className  = 'route-banner ' + routeClass(recommendedRoute);

  // Breakdown Flowchart
  const breakdownStr = decisionBreakdown || '';
  const flowContainer = document.getElementById('decision-flowchart');
  if (flowContainer) {
    flowContainer.innerHTML = '';
    if (!breakdownStr) {
      flowContainer.innerHTML = '<div class="flow-node"><div class="flow-content">No breakdown available.</div></div>';
    } else {
      const lines = breakdownStr.split('\n').map(l => l.trim()).filter(l => l);
      lines.forEach((line, idx) => {
        if (line === 'Decision Breakdown:') return;
        
        const node = document.createElement('div');
        node.className = 'flow-node';
        
        // Highlight keywords for better readability
        let formattedLine = line.substring(1).trim();
        formattedLine = formattedLine.replace(/→/g, '<strong style="color: var(--accent2);">→</strong>');
        formattedLine = formattedLine.replace(/:/g, ':<strong style="color: var(--text);">');
        
        if (line.startsWith('✔') || line.startsWith('✓')) {
           node.classList.add('node-pass');
           node.innerHTML = `
             <div class="node-icon">✓</div>
             <div class="flow-content">${formattedLine}</strong></div>
           `;
        } else if (line.startsWith('✘') || line.startsWith('⚠')) {
           node.classList.add('node-fail');
           node.innerHTML = `
             <div class="node-icon">${line[0]}</div>
             <div class="flow-content">${formattedLine}</strong></div>
           `;
        } else if (line.startsWith('Final Decision:')) {
           node.classList.add('node-final');
           node.innerHTML = `
             <div class="node-icon">🎯</div>
             <div class="flow-content">${line}</div>
           `;
        } else {
           node.innerHTML = `<div class="flow-content">${line}</div>`;
        }
        
        flowContainer.appendChild(node);
      });
    }
  }
  document.getElementById('reasoning-text').textContent = reasoning;

  // Metrics
  document.getElementById('m-assigned').textContent       = assignedTo || '—';
  document.getElementById('m-fraud').textContent          = fraudScore != null ? (fraudScore * 100).toFixed(0) + '%' : '—';
  document.getElementById('m-claim-type').textContent     = ef.other?.claim_type     || '—';
  document.getElementById('m-damage').textContent         = ef.asset_details?.estimated_damage != null
    ? '$' + Number(ef.asset_details.estimated_damage).toLocaleString() : '—';
  document.getElementById('m-missing').textContent        = missingFields.length;
  document.getElementById('m-policy').textContent         = ef.policy_info?.policy_number || '—';

  // Missing fields banner
  const missingBanner = document.getElementById('missing-banner');
  if (missingFields.length > 0) {
    missingBanner.style.display = 'flex';
    document.getElementById('missing-list').innerHTML =
      missingFields.map(f => `<li>${f}</li>`).join('');
  } else {
    missingBanner.style.display = 'none';
  }

  // Field sections
  renderSection('sec-policy', ef.policy_info || {}, {
    policy_number: 'Policy Number', policyholder_name: 'Policyholder',
    effective_date_start: 'Effective From', effective_date_end: 'Effective To',
  });
  renderSection('sec-incident', ef.incident_info || {}, {
    incident_date: 'Date', incident_time: 'Time',
    incident_location: 'Location', incident_description: 'Description',
  });
  renderSection('sec-parties', ef.involved_parties || {}, {
    claimant_name: 'Claimant', claimant_contact: 'Contact',
    third_parties: 'Third Parties', third_party_contacts: 'TP Contacts',
  });
  renderSection('sec-asset', ef.asset_details || {}, {
    asset_type: 'Asset Type', asset_id: 'Asset ID / VIN',
    estimated_damage: 'Estimated Damage',
  });
  renderSection('sec-other', ef.other || {}, {
    claim_type: 'Claim Type', initial_estimate: 'Initial Estimate',
    attachments: 'Attachments',
  });

  // Raw JSON
  jsonPre.innerHTML = syntaxHighlight(JSON.stringify(data, null, 2));

  // Show results
  resultsDiv.classList.add('show');
  resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderSection(id, data, labels) {
  const container = document.getElementById(id);
  if (!container) return;
  container.innerHTML = '';
  for (const [key, label] of Object.entries(labels)) {
    const val = data[key];
    const row = document.createElement('div');
    row.className = 'field-row';

    let displayVal;
    if (val === null || val === undefined) {
      displayVal = `<span class="field-val field-null">—</span>`;
    } else if (Array.isArray(val)) {
      displayVal = val.length ? `<span class="field-val">${val.join(', ')}</span>`
                              : `<span class="field-val field-null">None</span>`;
    } else if (key === 'estimated_damage' || key === 'initial_estimate') {
      displayVal = `<span class="field-val">$${Number(val).toLocaleString()}</span>`;
    } else if (key === 'incident_description') {
      displayVal = `<span class="field-val" style="max-width:70%;font-size:.78rem;line-height:1.5">${val}</span>`;
    } else {
      displayVal = `<span class="field-val">${val}</span>`;
    }

    row.innerHTML = `<span class="field-key">${label}</span>${displayVal}`;
    container.appendChild(row);
  }
}

function routeClass(route) {
  const map = {
    'Fast-track': 'route-fast',
    'Manual Review': 'route-manual',
    'Investigation': 'route-invest',
    'Specialist Queue': 'route-special',
    'Standard Processing': 'route-standard',
  };
  return map[route] || 'route-standard';
}

// ── JSON toggle ───────────────────────────────────────────────────────────
jsonToggle.addEventListener('click', () => {
  jsonBox.classList.toggle('open');
  jsonToggle.textContent = jsonBox.classList.contains('open') ? '📄 Hide Raw JSON' : '📄 View Raw JSON';
});

// ── Reset ─────────────────────────────────────────────────────────────────
btnReset.addEventListener('click', () => {
  clearFile();
  resultsDiv.classList.remove('show');
  progressSec.classList.remove('show');
  jsonBox.classList.remove('open');
  setAllSteps('idle');
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ── Syntax highlight ──────────────────────────────────────────────────────
function syntaxHighlight(json) {
  return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(\.\d+)?([eE][+-]?\d+)?)/g, match => {
    if (/^"/.test(match)) {
      return /:$/.test(match)
        ? `<span class="tok-key">${match}</span>`
        : `<span class="tok-str">${match}</span>`;
    }
    if (/true|false/.test(match)) return `<span class="tok-bool">${match}</span>`;
    if (/null/.test(match))       return `<span class="tok-null">${match}</span>`;
    return `<span class="tok-num">${match}</span>`;
  });
}

// ── Toast ─────────────────────────────────────────────────────────────────
function showToast(msg, type = 'info') {
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  requestAnimationFrame(() => t.classList.add('show'));
  setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 400); }, 4000);
}

// ── Employee Directory ────────────────────────────────────────────────────
const employeeGrid = document.getElementById('employee-grid');
const btnRefreshEmp = document.getElementById('btn-refresh-emp');

async function loadEmployees() {
  if (!employeeGrid) return;
  try {
    const res = await fetch(`${API_BASE}/employees`);
    if (!res.ok) throw new Error('Failed to fetch employees');
    const data = await res.json();
    
    employeeGrid.innerHTML = '';
    data.employees.forEach(emp => {
      const card = document.createElement('div');
      card.className = 'metric-card';
      
      let roleDisplay = emp.role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
      
      card.innerHTML = `
        <div class="metric-label">${roleDisplay}</div>
        <div class="metric-value">${emp.name}</div>
        <div class="metric-sub">Current Load: <strong>${emp.load}</strong> claims</div>
      `;
      employeeGrid.appendChild(card);
    });
  } catch (err) {
    console.error(err);
    employeeGrid.innerHTML = `<div style="color: var(--red); font-size: 0.9rem;">Error loading directory.</div>`;
  }
}

if (btnRefreshEmp) {
  btnRefreshEmp.addEventListener('click', () => {
    btnRefreshEmp.innerHTML = '↻ Refreshing...';
    loadEmployees().then(() => {
      setTimeout(() => btnRefreshEmp.innerHTML = '↻ Refresh Workload', 500);
    });
  });
}

// Initialize
document.addEventListener('DOMContentLoaded', loadEmployees);
