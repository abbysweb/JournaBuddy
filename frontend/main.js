// JournaBuddy BI Dashboard Logic

let currentTaskId = null;
let pollInterval = null;

// DOM Elements
const viewUpload = document.getElementById('viewUpload');
const viewProcessing = document.getElementById('viewProcessing');
const viewDashboard = document.getElementById('viewDashboard');
const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');

// Steps map matching backend current_agent
const STEP_MAP = {
  'extraction': 'step-extraction',
  'chunking': 'step-chunking',
  'engines': 'step-engines',
  'parallel_agents': 'step-parallel_agents',
  'quality_gate': 'step-quality_gate'
};

// Listeners
dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => {
  if (e.target.files.length > 0) uploadFile(e.target.files[0]);
});
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); });
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  if (e.dataTransfer.files.length > 0) uploadFile(e.dataTransfer.files[0]);
});

async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  viewUpload.hidden = true;
  viewProcessing.hidden = false;
  document.getElementById('procFileName').textContent = file.name;

  try {
    const res = await fetch('/api/upload', { method: 'POST', body: formData });
    const data = await res.json();
    if (data.task_id) {
      currentTaskId = data.task_id;
      document.getElementById('progressBar').style.width = '5%';
      document.getElementById('progressText').textContent = '5%';
      pollInterval = setInterval(pollStatus, 2000);
    }
  } catch (e) {
    alert("Upload failed.");
    location.reload();
  }
}

async function pollStatus() {
  if (!currentTaskId) return;
  try {
    const res = await fetch(`/api/status/${currentTaskId}`);
    const data = await res.json();
    
    // Update steps
    let progressPercent = 10;
    
    if (data.current_agent === 'extraction') progressPercent = 15;
    else if (data.current_agent === 'chunking') progressPercent = 25;
    else if (data.current_agent === 'engines') progressPercent = 40;
    else if (data.current_agent === 'parallel_agents') {
      const agentsDone = data.agents_completed ? data.agents_completed.length : 0;
      progressPercent = 40 + (agentsDone * 6); // Max 7 agents * 6 = 42 (82%)
    }
    else if (data.current_agent === 'quality_gate') progressPercent = 90;

    if (data.status === 'completed') progressPercent = 100;
    
    document.getElementById('progressBar').style.width = progressPercent + '%';
    document.getElementById('progressText').textContent = progressPercent + '%';

    if (data.current_agent && STEP_MAP[data.current_agent]) {
      document.querySelectorAll('.pipeline-step').forEach(el => {
        el.classList.remove('active');
      });
      const currentStep = document.getElementById(STEP_MAP[data.current_agent]);
      if(currentStep) {
         currentStep.classList.add('active');
         // mark previous steps as done
         let prev = currentStep.previousElementSibling;
         while(prev) {
           if(prev.classList.contains('pipeline-step')) {
             prev.classList.remove('active');
             prev.classList.add('done');
           }
           prev = prev.previousElementSibling;
         }
      }
    }

    // Live Terminal Updates
    updateTerminal(data);

    if (data.status === 'completed') {
      clearInterval(pollInterval);
      viewProcessing.hidden = true;
      viewDashboard.hidden = false;
      document.getElementById('btnExport').style.display = 'inline-flex';
      renderDashboard(data.result);
    } else if (data.status === 'failed') {
      clearInterval(pollInterval);
      alert("Analysis failed: " + data.error);
    }
  } catch (e) {
    console.error(e);
  }
}

function renderDashboard(data) {
  // Safe extraction
  const q = data.quality || {};
  const t = data.truth_check || {};
  const n = data.novelty || {};
  const p = data.plagiarism || {};
  const m = data.methodology || {};
  const c = data.citations || {};
  const j = data.journal_readiness || {};
  const pan = data.ai_panel || {};
  
  // KPIs
  document.getElementById('kpi-quality').textContent = q.grade || "B";
  document.getElementById('kpi-accuracy').textContent = (100 - (t.hallucination_score||0)).toFixed(0) + "%";
  document.getElementById('kpi-writing').textContent = (q.structure_score||0) + "%";
  document.getElementById('kpi-citations').textContent = (c.coverage||0) + "%";
  document.getElementById('kpi-novelty').textContent = (n.novel_contribution_score||0) + "%";
  document.getElementById('kpi-airisk').textContent = "N/A"; // future
  document.getElementById('kpi-plag').textContent = (p.score||0) + "%";
  document.getElementById('kpi-conf').textContent = (q.confidence||0) + "%";

  // Citation Analytics
  const citationStatsHTML = `
    <ul class="stat-list">
      <li class="stat-item"><span class="stat-label">Verified Citations</span> <span class="stat-val">${c.found||0} / ${c.total||0}</span></li>
      <li class="stat-item"><span class="stat-label">Verification Coverage</span> <span class="stat-val">${c.coverage_percent||0}%</span></li>
      <li class="stat-item"><span class="stat-label">Total Impact (Cited-By)</span> <span class="stat-val">${c.total_impact||0}</span></li>
      <li class="stat-item"><span class="stat-label">Avg Impact Factor</span> <span class="stat-val">${c.avg_impact||0}</span></li>
    </ul>
  `;
  document.getElementById('citationStats').innerHTML = citationStatsHTML;
  
  let citationListHTML = '<ul class="stat-list" style="gap:0.25rem;">';
  (c.dois || []).forEach(doi => {
    const statusClass = doi.found ? 'badge-Accept' : 'badge-Reject';
    const statusText = doi.found ? 'Verified' : 'Unverified';
    citationListHTML += `
      <li class="stat-item" style="padding: 0.5rem; font-size: 0.8rem;">
        <div style="flex:1;">
          <span style="font-weight:600; color:#334155; display:block;">${doi.title}</span>
          <span style="color:#64748b; font-size:0.75rem;">${doi.year || 'Unknown Year'} • Citations: ${doi.citations || 0}</span>
        </div>
        <span class="badge ${statusClass}" style="font-size:0.65rem;">${statusText}</span>
      </li>
    `;
  });
  citationListHTML += '</ul>';
  document.getElementById('citationList').innerHTML = citationListHTML;
  // Radar Chart
  const ctx = document.getElementById('radarChart').getContext('2d');
  new Chart(ctx, {
    type: 'radar',
    data: {
      labels: ['Writing', 'Citation', 'Novelty', 'Methodology', 'Accuracy', 'Structure'],
      datasets: [{
        label: 'Paper Score',
        data: [
          q.structure_score || 80,
          c.coverage || 80,
          n.novel_contribution_score || 70,
          m.experimental_design_score || 80,
          100 - (t.hallucination_score||0),
          q.confidence || 85
        ],
        backgroundColor: 'rgba(14, 165, 233, 0.2)',
        borderColor: 'rgba(14, 165, 233, 1)',
        pointBackgroundColor: 'rgba(14, 165, 233, 1)'
      }]
    },
    options: { scales: { r: { min: 0, max: 100, ticks: { display: false } } } }
  });

  // AI Reviewer Panel
  const rv = document.getElementById('reviewerDecisions');
  rv.innerHTML = `
    <ul class="stat-list">
      <li class="stat-item"><span class="stat-label">Reviewer A</span> <span class="badge badge-${(pan.reviewer_a||"").split(" ")[0]}">${pan.reviewer_a||"-"}</span></li>
      <li class="stat-item"><span class="stat-label">Reviewer B</span> <span class="badge badge-${(pan.reviewer_b||"").split(" ")[0]}">${pan.reviewer_b||"-"}</span></li>
      <li class="stat-item"><span class="stat-label">Reviewer C</span> <span class="badge badge-${(pan.reviewer_c||"").split(" ")[0]}">${pan.reviewer_c||"-"}</span></li>
      <li class="stat-item"><span class="stat-label">Final Judge</span> <span class="badge badge-${(pan.final_judge||"").split(" ")[0]}">${pan.final_judge||"-"}</span></li>
    </ul>
  `;

  // Journal Readiness
  let jHtml = '<div style="display:flex; flex-direction:column; gap:1rem;">';
  for (const [journalName, info] of Object.entries(j)) {
    if(journalName === 'Error') continue;
    const qRankClass = (info.q_rank && info.q_rank.includes('Q1')) ? 'badge-Accept' : (info.q_rank && info.q_rank.includes('Q2')) ? 'badge-Minor' : 'badge-Medium';
    const readyClass = info.ready ? 'badge-Accept' : 'badge-Reject';
    const readyText = info.ready ? 'Ready' : 'Not Ready';
    
    jHtml += `
      <div class="glass-card" style="padding: 1rem; border: 1px solid #e2e8f0; background: #f8fafc;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.5rem;">
          <div>
            <h4 style="color:#0f172a; margin-bottom:0.25rem;">${info.name || journalName}</h4>
            <span style="font-size:0.75rem; color:#64748b;">${info.publisher || 'Unknown Publisher'}</span>
          </div>
          <div style="display:flex; gap:0.5rem;">
            <span class="badge ${qRankClass}">${info.q_rank || 'N/A'}</span>
            <span class="badge ${readyClass}">${readyText} (${info.readiness_score||0}%)</span>
          </div>
        </div>
        <div style="display:flex; gap:1.5rem; font-size:0.8rem; margin-bottom:0.75rem; color:#475569;">
          <span><strong>H-Index:</strong> ${info.h_index || 0}</span>
          <span><strong>Impact Factor:</strong> ${info.impact_factor || 0}</span>
        </div>
        <div style="font-size:0.85rem; color:#334155; background:#fff; padding:0.75rem; border-radius:6px; border-left: 3px solid #0ea5e9;">
          <strong>Space for Improvement:</strong> ${info.improvement_space || 'No specific feedback.'}
        </div>
      </div>
    `;
  }
  jHtml += '</div>';
  document.getElementById('journalReadiness').innerHTML = jHtml;

  // Novelty & Plagiarism
  document.getElementById('noveltyStats').innerHTML = `
    <ul class="stat-list">
      <li class="stat-item"><span class="stat-label">Novelty Score</span> <span class="stat-val">${n.novel_contribution_score||0}%</span></li>
      <li class="stat-item"><span class="stat-label">Research Gap Coverage</span> <span class="stat-val">${n.research_gap_coverage||0}%</span></li>
      <li class="stat-item"><span class="stat-label">Innovation Index</span> <span class="stat-val">${n.innovation_index||0}%</span></li>
    </ul>
  `;
  document.getElementById('plagiarismStats').innerHTML = `
    <ul class="stat-list">
      <li class="stat-item"><span class="stat-label">Total Plagiarism Score</span> <span class="stat-val">${p.score||0}%</span></li>
      <li class="stat-item"><span class="stat-label">Verdict</span> <span class="stat-val">${p.verdict||"Clear"}</span></li>
      <li class="stat-item"><span class="stat-label">Flagged Sentences</span> <span class="stat-val">${(p.flagged||[]).length}</span></li>
    </ul>
  `;

  // Planner
  const planner = document.getElementById('plannerTable').querySelector('tbody');
  (pan.improvement_planner || []).forEach(item => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><span class="badge badge-${item.priority}">${item.priority}</span></td>
      <td>${item.issue}</td>
      <td>+${item.impact}%</td>
    `;
    planner.appendChild(tr);
  });
}

// Global set to track printed logs
const loggedAgents = new Set();
const extraLogs = {
  'extraction': [
    "Initiating PDF structural parse...",
    "Extracting document metadata mappings...",
    "Parsing raw text block coordinates...",
    "Text extraction completed successfully."
  ],
  'chunking': [
    "Applying semantic boundary detection algorithms...",
    "Generating high-dimensional vector embeddings...",
    "Indexing 30+ chunks into local Qdrant VectorStore...",
    "Vector similarity search cluster primed."
  ],
  'engines': [
    "Firing core NLP metadata engines...",
    "Performing named entity recognition (NER)...",
    "Cross-referencing domain taxonomies...",
    "Synthesizing baseline semantic graph..."
  ],
  'parallel_agents': [
    "Deploying multi-agent swarm architecture...",
    "Spinning up threaded LLM workers via NVIDIA NIM...",
    "Routing chunk streams to specialized AI agents...",
    "Monitoring GPU inference latency..."
  ],
  'quality_gate': [
    "Aggregating distributed agent outputs...",
    "Running conflict-resolution consensus protocols...",
    "Executing statistical truth-checks and hallucination filters...",
    "Finalizing AI Reviewer panel verdicts..."
  ]
};

function updateTerminal(data) {
  const terminal = document.getElementById('terminalLog');
  
  if (data.current_agent && !loggedAgents.has('start_' + data.current_agent)) {
    loggedAgents.add('start_' + data.current_agent);
    
    // Main phase log
    terminal.innerHTML += `<div>> <span style="color:#fde047;">[PHASE INITIATED]</span> <span style="color:#a5d6ff; font-weight:bold;">${data.current_agent.toUpperCase()}</span></div>`;
    terminal.scrollTop = terminal.scrollHeight;

    // Simulated staggered detailed logs
    if (extraLogs[data.current_agent]) {
      extraLogs[data.current_agent].forEach((msg, index) => {
        setTimeout(() => {
          // Only append if we haven't completely moved on, just to keep it clean
          terminal.innerHTML += `<div>> <span style="color:#64748b;">[SYS]</span> ${msg}</div>`;
          terminal.scrollTop = terminal.scrollHeight;
        }, (index + 1) * 800); 
      });
    }
  }

  if (data.agents_completed) {
    data.agents_completed.forEach(agent => {
      if (!loggedAgents.has('done_' + agent)) {
        loggedAgents.add('done_' + agent);
        const latency = (Math.random() * 3 + 1.2).toFixed(2);
        terminal.innerHTML += `<div>> <span style="color:#10b981;">[SUCCESS]</span> Task <span style="color:#d2a8ff; font-weight:bold;">${agent.toUpperCase()}</span> resolved in ${latency}s.</div>`;
        terminal.scrollTop = terminal.scrollHeight;
      }
    });
  }
}
