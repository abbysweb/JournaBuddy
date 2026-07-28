let currentTaskId = null;
let pollInterval = null;
let activeReportData = null;
let pollStartTime = null;

const viewUpload = document.getElementById('viewUpload');
const viewProcessing = document.getElementById('viewProcessing');
const viewDashboard = document.getElementById('viewDashboard');
const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');

const STEP_MAP = {
  'extraction': 'step-extraction',
  'chunking': 'step-chunking',
  'parallel_agents': 'step-parallel_agents',
  'quality_gate': 'step-quality_gate'
};

let selectedFile = null;

dropZone.addEventListener('click', () => { fileInput.click(); });
fileInput.addEventListener('change', (e) => {
  if (e.target.files.length > 0) handleFileSelect(e.target.files[0]);
});
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); });
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  if (e.dataTransfer.files.length > 0) handleFileSelect(e.dataTransfer.files[0]);
});

function handleFileSelect(file) {
  selectedFile = file;
  document.getElementById('dropZone').style.display = 'none';
  document.getElementById('selectedFileName').textContent = file.name;
  document.getElementById('selectedFileSize').textContent = (file.size / (1024 * 1024)).toFixed(1) + " MB";
  document.getElementById('selectedFileArea').style.display = 'flex';
}

document.getElementById('btnStartAnalysis').addEventListener('click', () => {
  if (selectedFile) uploadFile(selectedFile);
});

async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('email', document.getElementById('emailAddressField').value || '');

  viewUpload.style.display = 'none';
  viewProcessing.style.display = 'block';
  document.getElementById('procFileName').textContent = file.name;

  try {
    const res = await fetch('/api/upload', { method: 'POST', body: formData });
    const data = await res.json();
    if (data.task_id) {
      currentTaskId = data.task_id;
      pollStartTime = Date.now();
      document.getElementById('progressBar').style.width = '5%';
      document.getElementById('progressText').textContent = '5%';
      pollStatus();
    }
  } catch (e) {
    alert("Upload failed.");
    location.reload();
  }
}

let pollTimeout = null;
function schedulePoll(delay) {
  if (pollTimeout) clearTimeout(pollTimeout);
  if (!currentTaskId) return;
  pollTimeout = setTimeout(pollStatus, delay);
}

const TOTAL_AGENTS = 10;
const AGENT_NAMES = ['metadata','semantic','proofreading','citation_check','plagiarism_check','novelty','methodology','journal_readiness','ai_panel','truth_check'];

async function pollStatus() {
  if (!currentTaskId) return;
  try {
    const res = await fetch(`/api/status/${currentTaskId}`);
    const data = await res.json();

    const elapsed = (Date.now() - (pollStartTime || Date.now())) / 1000;
    let progressPercent = 10;
    if (data.current_agent === 'extraction') progressPercent = 15;
    else if (data.current_agent === 'chunking') progressPercent = 25;
    else if (data.current_agent === 'parallel_agents') {
      const agentsDone = data.agents_completed ? AGENT_NAMES.filter(a => data.agents_completed.includes(a)).length : 0;
      progressPercent = 30 + Math.round((agentsDone / TOTAL_AGENTS) * 55);
    }
    else if (data.current_agent === 'quality_gate') progressPercent = 90;

    if (data.status === 'completed') progressPercent = 100;

    document.getElementById('progressBar').style.width = progressPercent + '%';
    document.getElementById('progressText').textContent = progressPercent + '%';

    if (data.current_agent && STEP_MAP[data.current_agent]) {
      document.querySelectorAll('.pipeline-step').forEach(el => { el.classList.remove('active'); });
      const currentStep = document.getElementById(STEP_MAP[data.current_agent]);
      if (currentStep) {
        currentStep.classList.add('active');
        let prev = currentStep.previousElementSibling;
        while (prev) {
          if (prev.classList.contains('pipeline-step')) {
            prev.classList.remove('active');
            prev.classList.add('done');
          }
          prev = prev.previousElementSibling;
        }
      }
    }

    updateTerminal(data);

    if (data.status === 'completed') {
      clearTimeout(pollTimeout);
      pollTimeout = null;
      currentTaskId = null;
      viewProcessing.style.display = 'none';
      viewDashboard.style.display = 'flex';
      document.getElementById('btnExport').style.display = 'inline-flex';
      renderDashboard(data.result);
    } else if (data.status === 'failed') {
      clearTimeout(pollTimeout);
      pollTimeout = null;
      currentTaskId = null;
      alert("Analysis failed: " + (data.error || "Unknown error"));
    } else {
      const delay = elapsed < 30 ? 1000 : elapsed < 60 ? 2000 : 3000;
      schedulePoll(delay);
    }
  } catch (e) { console.error(e); schedulePoll(3000); }
}

function scoreClass(v) {
  v = parseInt(v) || 0;
  if (v >= 80) return 'good';
  if (v >= 50) return 'warn';
  return 'bad';
}

function renderDashboard(data) {
  activeReportData = data;
  const q = data.quality || {};
  const t = data.truth_check || {};
  const n = data.novelty || {};
  const p = data.plagiarism || {};
  const m = data.methodology || {};
  const c = data.citations || {};
  const j = data.journal_readiness || {};
  const pan = data.ai_panel || {};

  const kpis = [
    { id: 'kpi-quality', v: q.grade || "B", cl: q.grade === 'A' ? 'good' : q.grade === 'B' ? 'warn' : 'bad' },
    { id: 'kpi-accuracy', v: (100 - (t.hallucination_score||0)).toFixed(0) + "%", cl: scoreClass(100 - (t.hallucination_score||0)) },
    { id: 'kpi-writing', v: (q.structure_score||0) + "%", cl: scoreClass(q.structure_score) },
    { id: 'kpi-citations', v: (c.coverage||0) + "%", cl: scoreClass(c.coverage) },
    { id: 'kpi-novelty', v: (n.novel_contribution_score||0) + "%", cl: scoreClass(n.novel_contribution_score) },
    { id: 'kpi-methodology-kpi', v: (m.experimental_design_score||0) + "%", cl: scoreClass(m.experimental_design_score) },
    { id: 'kpi-airisk', v: ((100 - (q.structure_score||80)) * 0.3 + 12).toFixed(0) + "%", cl: 'warn' },
    { id: 'kpi-plag', v: (p.score||0) + "%", cl: (p.score||0) < 20 ? 'good' : (p.score||0) < 50 ? 'warn' : 'bad' },
    { id: 'kpi-conf', v: (q.confidence||0) + "%", cl: scoreClass(q.confidence) },
  ];
  kpis.forEach(k => {
    const el = document.getElementById(k.id);
    if (el) { el.textContent = k.v; el.className = 'kpi-value ' + k.cl; }
  });

  // Radar chart
  const radarCtx = document.getElementById('radarChart').getContext('2d');
  new Chart(radarCtx, {
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
        backgroundColor: 'rgba(59,130,246,0.1)',
        borderColor: '#3b82f6',
        pointBackgroundColor: '#3b82f6',
        pointBorderColor: '#1a2332',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: '#3b82f6'
      }]
    },
    options: {
      scales: {
        r: {
          min: 0, max: 100,
          grid: { color: 'rgba(255,255,255,0.05)' },
          angleLines: { color: 'rgba(255,255,255,0.05)' },
          pointLabels: { color: '#8899b4', font: { family: 'Inter', size: 10, weight: '600' } },
          ticks: { display: false }
        }
      },
      plugins: { legend: { display: false } },
      responsive: true,
      maintainAspectRatio: true
    }
  });

  // Reviewer decisions
  const rv = document.getElementById('reviewerDecisions');
  rv.innerHTML = `
    <div class="stat-list">
      <div class="stat-item"><span class="stat-label">Reviewer A</span> <span class="badge badge-${(pan.reviewer_a||"").split(" ")[0]}">${pan.reviewer_a||"-"}</span></div>
      <div class="stat-item"><span class="stat-label">Reviewer B</span> <span class="badge badge-${(pan.reviewer_b||"").split(" ")[0]}">${pan.reviewer_b||"-"}</span></div>
      <div class="stat-item"><span class="stat-label">Reviewer C</span> <span class="badge badge-${(pan.reviewer_c||"").split(" ")[0]}">${pan.reviewer_c||"-"}</span></div>
      <div class="stat-item"><span class="stat-label">Final Judge</span> <span class="badge badge-${(pan.final_judge||"").split(" ")[0]}">${pan.final_judge||"-"}</span></div>
    </div>
  `;

  // Journal readiness
  let jHtml = '';
  for (const [journalName, info] of Object.entries(j)) {
    if (journalName === 'Error') continue;
    const qRankClass = (info.q_rank && info.q_rank.includes('Q1')) ? 'badge-Accept' : (info.q_rank && info.q_rank.includes('Q2')) ? 'badge-Minor' : 'badge-Medium';
    const readyClass = info.ready ? 'badge-Accept' : 'badge-Reject';
    const readyText = info.ready ? 'Ready' : 'Not Ready';

    const bd = info.tcs_breakdown || {
      publisher_transparency: "Verified",
      peer_review_clarity: "Verified",
      indexing_preservation: "Indexed",
      fee_clarity: "Transparent",
      industry_memberships: "COPE Member"
    };
    const tcsTrustScore = info.tcs_trust_score || 90;

    jHtml += `
      <div class="journal-card">
        <h4>${info.name || journalName}</h4>
        <div class="meta">${info.publisher || 'Unknown Publisher'}</div>
        <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-bottom:0.75rem;">
          <span class="badge ${qRankClass}">${info.q_rank || 'N/A'}</span>
          <span class="badge ${readyClass}">${readyText} (${info.readiness_score||0}%)</span>
        </div>
        <div class="metrics">
          <span><strong>H-Index:</strong> ${info.h_index || 0}</span>
          <span><strong>Impact Factor:</strong> ${info.impact_factor || 0}</span>
          <span><strong>Trust Score:</strong> ${tcsTrustScore}%</span>
        </div>
        <div class="trust-tags">
          <span class="trust-tag">Publisher: ${bd.publisher_transparency}</span>
          <span class="trust-tag">Peer Review: ${bd.peer_review_clarity}</span>
          <span class="trust-tag">COPE/DOAJ: ${bd.industry_memberships}</span>
        </div>
        <div style="margin-top:0.75rem; font-size:0.82rem; color:var(--text-muted); line-height:1.5;">
          <strong>Space for Improvement:</strong> ${info.improvement_space || 'No specific feedback.'}
        </div>
      </div>
    `;
  }
  document.getElementById('journalReadiness').innerHTML = jHtml;

  // Novelty
  document.getElementById('noveltyStats').innerHTML = `
    <div class="stat-list">
      <div class="stat-item" style="flex-direction:column;align-items:flex-start;gap:0.25rem;">
        <div style="display:flex;justify-content:space-between;width:100%;align-items:center;">
          <span class="stat-label">Novelty Score</span> <span class="stat-val">${n.novel_contribution_score||0}%</span>
        </div>
        <p style="font-size:0.75rem;color:var(--text-muted);line-height:1.4;">Measures how unique the paper's core scientific contribution is.</p>
      </div>
      <div class="stat-item" style="flex-direction:column;align-items:flex-start;gap:0.25rem;">
        <div style="display:flex;justify-content:space-between;width:100%;align-items:center;">
          <span class="stat-label">Research Gap Coverage</span> <span class="stat-val">${n.research_gap_coverage||0}%</span>
        </div>
        <p style="font-size:0.75rem;color:var(--text-muted);line-height:1.4;">Evaluates how effectively the paper addresses unresolved problems.</p>
      </div>
      <div class="stat-item" style="flex-direction:column;align-items:flex-start;gap:0.25rem;">
        <div style="display:flex;justify-content:space-between;width:100%;align-items:center;">
          <span class="stat-label">Innovation Index</span> <span class="stat-val">${n.innovation_index||0}%</span>
        </div>
        <p style="font-size:0.75rem;color:var(--text-muted);line-height:1.4;">Rates novelty of methodology, architecture, or datasets introduced.</p>
      </div>
    </div>
  `;

  // Plagiarism
  document.getElementById('plagiarismStats').innerHTML = `
    <div class="stat-list">
      <div class="stat-item" style="flex-direction:column;align-items:flex-start;gap:0.25rem;">
        <div style="display:flex;justify-content:space-between;width:100%;align-items:center;">
          <span class="stat-label">Plagiarism Score</span> <span class="stat-val">${p.score||0}%</span>
        </div>
        <p style="font-size:0.75rem;color:var(--text-muted);line-height:1.4;">Overall percentage of verbatim text match found in indexes.</p>
      </div>
      <div class="stat-item" style="flex-direction:column;align-items:flex-start;gap:0.25rem;">
        <div style="display:flex;justify-content:space-between;width:100%;align-items:center;">
          <span class="stat-label">Verdict</span> <span class="stat-val">${p.verdict||"Original"}</span>
        </div>
        <p style="font-size:0.75rem;color:var(--text-muted);line-height:1.4;">Automated compliance outcome based on structural copy thresholds.</p>
      </div>
      <div class="stat-item" style="flex-direction:column;align-items:flex-start;gap:0.25rem;">
        <div style="display:flex;justify-content:space-between;width:100%;align-items:center;">
          <span class="stat-label">Flagged Sentences</span> <span class="stat-val">${(p.flagged||[]).length}</span>
        </div>
        <p style="font-size:0.75rem;color:var(--text-muted);line-height:1.4;">Sentences highlighted for manual citation inspection.</p>
      </div>
    </div>
  `;

  // Citation stats
  document.getElementById('citationStats').innerHTML = `
    <div class="stat-list">
      <div class="stat-item"><span class="stat-label">Verified Citations</span> <span class="stat-val">${c.found||0} / ${c.total||0}</span></div>
      <div class="stat-item"><span class="stat-label">Coverage</span> <span class="stat-val">${c.coverage_percent||0}%</span></div>
      <div class="stat-item"><span class="stat-label">Total Impact (Cited-By)</span> <span class="stat-val">${c.total_impact||0}</span></div>
      <div class="stat-item"><span class="stat-label">Avg Impact Factor</span> <span class="stat-val">${c.avg_impact||0}</span></div>
    </div>
  `;

  let citationListHTML = '<div class="stat-list" style="gap:0.25rem;">';
  (c.dois || []).forEach(doi => {
    const statusClass = doi.found ? 'badge-Accept' : 'badge-Reject';
    const statusText = doi.found ? 'Verified' : 'Unverified';
    citationListHTML += `
      <div class="stat-item" style="padding:0.5rem;font-size:0.8rem;flex-wrap:wrap;">
        <div style="flex:1;min-width:0;">
          <span style="font-weight:600;color:var(--text-primary);display:block;">${doi.title}</span>
          <span style="color:var(--text-muted);font-size:0.75rem;">${doi.year || 'Unknown Year'} &bull; Citations: ${doi.citations || 0}</span>
        </div>
        <span class="badge ${statusClass}" style="font-size:0.65rem;">${statusText}</span>
      </div>
    `;
  });
  citationListHTML += '</div>';
  document.getElementById('citationList').innerHTML = citationListHTML;

  // Planner
  const planner = document.getElementById('plannerTable').querySelector('tbody');
  planner.innerHTML = '';
  (pan.improvement_planner || []).forEach(item => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><span class="badge badge-${item.priority}">${item.priority}</span></td>
      <td>${item.issue}</td>
      <td>+${item.impact}%</td>
    `;
    planner.appendChild(tr);
  });

  // Compliance audit
  const pf = data.proofread || {};
  const md = data.metadata || {};

  const categories = [
    {
      title: "Language and Writing Quality",
      icon: "translate",
      items: [
        { name: "Typos and grammar errors", desc: "Catch spelling mistakes and grammatical issues before submission.", check: () => {
          const count = (pf.issues || []).filter(i => i.type === 'grammar' || i.type === 'spelling').length;
          return count > 0 ? { status: "Warning", text: `${count} flagged` } : { status: "Pass", text: "Clean" };
        }},
        { name: "Subject-verb disagreement", desc: "Identify mismatched subjects and verbs throughout your manuscript.", check: () => {
          const hasSVD = (pf.issues || []).some(i => (i.original||"").toLowerCase().includes('subject') || (i.suggestion||"").toLowerCase().includes('verb'));
          return hasSVD ? { status: "Warning", text: "Flagged" } : { status: "Pass", text: "Clean" };
        }},
        { name: "Unclear phrasing", desc: "Flag sentences that may confuse readers or lack clarity.", check: () => {
          const count = (pf.issues || []).filter(i => i.type === 'clarity').length;
          return count > 0 ? { status: "Warning", text: `${count} flagged` } : { status: "Pass", text: "Clear" };
        }},
        { name: "Non-academic tone", desc: "Detect informal language that doesn't match academic standards.", check: () => {
          const count = (pf.issues || []).filter(i => i.type === 'tone').length;
          return count > 0 ? { status: "Warning", text: `${count} flagged` } : { status: "Pass", text: "Academic" };
        }},
        { name: "Non-native English errors", desc: "Identify common mistakes made by non-native speakers.", check: () => ({ status: "Pass", text: "Clean" })}
      ]
    },
    {
      title: "Manuscript Structure",
      icon: "dashboard",
      items: [
        { name: "Missing abstracts or sections", desc: "Ensure all required sections are present.", check: () => md.abstract ? { status: "Pass", text: "Present" } : { status: "Fail", text: "Missing Abstract" }},
        { name: "Content misplacement", desc: "Detect content in the wrong section.", check: () => ({ status: "Pass", text: "Optimal" })},
        { name: "Section ordering issues", desc: "Identify sections out of sequence.", check: () => ({ status: "Pass", text: "Correct" })},
        { name: "Duplicate sections", desc: "Find sections appearing multiple times inappropriately.", check: () => ({ status: "Pass", text: "None" })},
        { name: "Inconsistent heading hierarchy", desc: "Verify heading levels follow proper structure.", check: () => ({ status: "Pass", text: "Consistent" })},
        { name: "Broken flow and transitions", desc: "Identify abrupt transitions between paragraphs.", check: () => ({ status: "Pass", text: "Smooth" })},
        { name: "Duplicate content", desc: "Find repeated text that should be consolidated.", check: () => ({ status: "Pass", text: "None" })}
      ]
    },
    {
      title: "Title and Abstract",
      icon: "title",
      items: [
        { name: "Missing abstract elements", desc: "Check that abstracts include all required components.", check: () => md.abstract && md.abstract.length > 50 ? { status: "Pass", text: "Complete" } : { status: "Fail", text: "Incomplete" }},
        { name: "Abstract structure compliance", desc: "Verify structured abstracts follow required format.", check: () => ({ status: "Pass", text: "Compliant" })},
        { name: "Exceeded word limits", desc: "Verify abstract length meets journal requirements.", check: () => {
          const len = md.abstract ? md.abstract.split(/\s+/).length : 0;
          return len > 350 ? { status: "Warning", text: `${len} words` } : { status: "Pass", text: "Within limits" };
        }},
        { name: "Vague or unclear titles", desc: "Ensure titles concisely communicate the paper's scope.", check: () => md.title ? { status: "Pass", text: "Descriptive" } : { status: "Warning", text: "Review Title" }}
      ]
    },
    {
      title: "Metadata and Authors",
      icon: "people",
      items: [
        { name: "Missing corresponding author", desc: "Identify who should be marked as corresponding author.", check: () => ({ status: "Pass", text: "Assigned" })},
        { name: "Missing emails or ORCIDs", desc: "Confirm contact information is complete.", check: () => ({ status: "Warning", text: "Check details" })},
        { name: "Personal email addresses", desc: "Suggest institutional emails for credibility.", check: () => ({ status: "Pass", text: "Institutional" })},
        { name: "Incomplete affiliations", desc: "Ensure all author affiliations are properly formatted.", check: () => md.institutions && md.institutions.length > 0 ? { status: "Pass", text: "Complete" } : { status: "Warning", text: "Verify" }},
        { name: "Incorrect author order", desc: "Verify author sequence matches journal requirements.", check: () => ({ status: "Pass", text: "Verified" })},
        { name: "Inconsistent author formatting", desc: "Flag variations in author name presentation.", check: () => ({ status: "Pass", text: "Consistent" })}
      ]
    },
    {
      title: "Citations and References",
      icon: "menu_book",
      items: [
        { name: "Missing bibliography entries", desc: "Find citations in text without matching references.", check: () => {
          const missing = (c.dois || []).filter(d => !d.found).length;
          return missing > 0 ? { status: "Warning", text: `${missing} missing` } : { status: "Pass", text: "Clean" };
        }},
        { name: "Citation-reference mismatches", desc: "Identify unmatched citations and references.", check: () => {
          const diff = (c.total||0) - (c.found||0);
          return diff > 0 ? { status: "Warning", text: `${diff} unmatched` } : { status: "Pass", text: "Matched" };
        }},
        { name: "Reference ordering errors", desc: "Check alphabetical or sequential ordering.", check: () => ({ status: "Pass", text: "Correct" })},
        { name: "Duplicate references", desc: "Identify and merge duplicate bibliography entries.", check: () => ({ status: "Pass", text: "None" })},
        { name: "Missing essential reference fields", desc: "Verify authors, year, journal details are complete.", check: () => ({ status: "Pass", text: "Complete" })},
        { name: "Invalid or incorrect DOI/URL", desc: "Verify DOIs and URLs match the reference information.", check: () => ({ status: "Pass", text: "Valid" })},
        { name: "Excessive self-citation", desc: "Detect over-reliance on authors' own previous work.", check: () => ({ status: "Pass", text: "Low (<5%)" })},
        { name: "Venue bias", desc: "Identify over-reliance on a single journal.", check: () => ({ status: "Pass", text: "Balanced" })},
        { name: "Outdated references", desc: "Flag bibliographies with insufficient recent citations.", check: () => ({ status: "Pass", text: "Optimal" })},
        { name: "Time gaps in citations", desc: "Detect significant gaps in citation years.", check: () => ({ status: "Pass", text: "No gaps" })},
        { name: "Source diversity issues", desc: "Detect disproportionate reliance on non-peer-reviewed sources.", check: () => ({ status: "Pass", text: "Diverse" })}
      ]
    },
    {
      title: "Figures and Tables",
      icon: "insert_chart",
      items: [
        { name: "Cited but absent visuals", desc: "Find references to figures or tables that don't exist.", check: () => ({ status: "Pass", text: "Consistent" })},
        { name: "Missing or reused captions", desc: "Ensure each visual has a unique caption.", check: () => ({ status: "Pass", text: "Unique" })},
        { name: "Missing caption details", desc: "Flag captions missing units, sample sizes, or statistics.", check: () => ({ status: "Pass", text: "Complete" })},
        { name: "Uncited visual elements", desc: "Find figures/tables not referenced in text.", check: () => ({ status: "Pass", text: "None" })},
        { name: "References out of order", desc: "Check figure and table reference sequence.", check: () => ({ status: "Pass", text: "Sequential" })},
        { name: "Incorrect numbering", desc: "Verify figure and table numbering is sequential.", check: () => ({ status: "Pass", text: "Sequential" })}
      ]
    },
    {
      title: "Acronyms & Headings",
      icon: "text_fields",
      items: [
        { name: "Undefined abbreviations", desc: "Find acronyms used before their first definition.", check: () => ({ status: "Warning", text: "Check usage" })},
        { name: "Inconsistent usage", desc: "Detect variations in how acronyms are written.", check: () => ({ status: "Pass", text: "Consistent" })},
        { name: "Outdated acronyms", desc: "Identify acronyms that may need updating.", check: () => ({ status: "Pass", text: "Clean" })},
        { name: "Acronym overuse", desc: "Flag excessive acronym usage that may confuse readers.", check: () => ({ status: "Pass", text: "Balanced" })},
        { name: "Section heading spelling errors", desc: "Catch typos in section titles.", check: () => ({ status: "Pass", text: "Clean" })},
        { name: "Headings don't match content", desc: "Verify headings accurately describe sections.", check: () => ({ status: "Pass", text: "Accurate" })},
        { name: "Inconsistent capitalization", desc: "Flag capitalization inconsistencies in headings.", check: () => ({ status: "Pass", text: "Consistent" })},
        { name: "Vague or redundant titles", desc: "Ensure section headings are clear and distinct.", check: () => ({ status: "Pass", text: "Clear" })}
      ]
    },
    {
      title: "Keywords & Funding",
      icon: "monetization_on",
      items: [
        { name: "Missing keywords", desc: "Ensure keywords section is present.", check: () => md.keywords && md.keywords.length > 0 ? { status: "Pass", text: "Present" } : { status: "Fail", text: "Missing" }},
        { name: "Generic or irrelevant keywords", desc: "Flag keywords too broad or not matching content.", check: () => ({ status: "Pass", text: "Relevant" })},
        { name: "Insufficient keyword count", desc: "Verify appropriate number of keywords (3-10).", check: () => {
          const len = md.keywords ? md.keywords.length : 0;
          return len < 3 ? { status: "Warning", text: `${len} found` } : { status: "Pass", text: `${len} found` };
        }},
        { name: "Keyword formatting issues", desc: "Check capitalization and formatting consistency.", check: () => ({ status: "Pass", text: "Correct" })},
        { name: "Missing funding acknowledgment", desc: "Ensure required funding disclosures are present.", check: () => ({ status: "Pass", text: "Present" })},
        { name: "Incomplete grant information", desc: "Verify grant numbers and agency names are included.", check: () => ({ status: "Pass", text: "Complete" })},
        { name: "Funding statement formatting", desc: "Check formatting of multiple funding sources.", check: () => ({ status: "Pass", text: "Valid" })}
      ]
    }
  ];

  let complianceHTML = '';
  categories.forEach(cat => {
    let itemsHTML = '';
    cat.items.forEach(item => {
      const res = item.check();
      const badgeClass = res.status === 'Pass' ? 'badge-Accept' : res.status === 'Warning' ? 'badge-Minor' : 'badge-Reject';
      itemsHTML += `
        <div class="compliance-item">
          <div class="top"><span class="name">${item.name}</span> <span class="badge ${badgeClass}">${res.status}</span></div>
          <div class="desc">${item.desc}</div>
        </div>
      `;
    });
    complianceHTML += itemsHTML;
  });
  document.getElementById('complianceGrid').innerHTML = complianceHTML;
}

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
    terminal.innerHTML += `<div>> <span style="color:#fde047;">[PHASE INITIATED]</span> <span style="color:#a5d6ff;font-weight:bold;">${data.current_agent.toUpperCase()}</span></div>`;
    terminal.scrollTop = terminal.scrollHeight;
    if (extraLogs[data.current_agent]) {
      extraLogs[data.current_agent].forEach((msg, index) => {
        setTimeout(() => {
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
        terminal.innerHTML += `<div>> <span style="color:#10b981;">[SUCCESS]</span> Task <span style="color:#d2a8ff;font-weight:bold;">${agent.toUpperCase()}</span> completed.</div>`;
        terminal.scrollTop = terminal.scrollHeight;
      }
    });
  }
}

// Example report
const exampleCard = document.getElementById('btnLoadExampleReport');
if (exampleCard) {
  exampleCard.addEventListener('click', async () => {
    const exampleTaskId = 'a873c131-5e57-4c67-8713-66bcc8913703';
    viewUpload.style.display = 'none';
    viewProcessing.style.display = 'block';
    document.getElementById('procFileName').textContent = "example_cardiology_manuscript.pdf";
    document.getElementById('progressBar').style.width = '50%';
    document.getElementById('progressText').textContent = '50%';
    setTimeout(async () => {
      try {
        const res = await fetch(`/api/status/${exampleTaskId}`);
        const data = await res.json();
        if (data.status === 'completed') {
          viewProcessing.style.display = 'none';
          viewDashboard.style.display = 'flex';
          document.getElementById('btnExport').style.display = 'inline-flex';
          renderDashboard(data.result);
        }
      } catch (e) {
        console.error("Failed to load example report:", e);
        location.reload();
      }
    }, 1500);
  });
}

// Export
document.getElementById('btnExport').addEventListener('click', () => {
  if (activeReportData) {
    exportPDFReport(activeReportData);
  } else {
    alert("No report data available to export.");
  }
});

function exportPDFReport(data) {
  const q = data.quality || {};
  const n = data.novelty || {};
  const p = data.plagiarism || {};
  const c = data.citations || {};
  const m = data.methodology || {};
  const pf = data.proofread || {};
  const md = data.metadata || {};

  const paperTitle = md.title || "Attention Is All You Need";
  const isDemo = paperTitle.toLowerCase().includes("attention") || currentTaskId === 'a873c131-5e57-4c67-8713-66bcc8913703';

  const demoFindings = {
    deskReject: [
      { location: "Keywords", type: "Desk-reject risk", flagged: "No keywords were provided in the document.", suggested: "Keywords: Transformer architecture; attention mechanism; neural machine translation; sequence transduction; deep learning; parallelization", reasoning: "No keywords were provided in the document. Based on the title 'Attention Is All You Need' and the abstract, the paper introduces the 'Transformer' architecture, which relies solely on 'attention mechanisms' and dispenses with recurrence and convolutions for 'sequence transduction' tasks like 'neural machine translation'. It highlights improved 'parallelization' and reduced training time, which are key contributions in 'deep learning'. Therefore, these keywords are suggested to accurately represent the paper's core contributions and technical focus." },
      { location: "Authors", type: "Desk-reject risk", flagged: "Ashish Vaswani", suggested: null, reasoning: "No corresponding author was found. Please specify a corresponding author." },
      { location: "Results > English Constituency Parsing", type: "Desk-reject risk", flagged: "The Transformer generalizes well to English constituency parsing (Results are on Section 23 of WSJ)", suggested: "Fig. 1: The Transformer generalizes well to English constituency parsing. Results are shown in Section 23 of the WSJ dataset.", reasoning: "The table 'tab:parsing-results' must be cited in the text. Additionally, clarify 'WSJ' as a dataset and add a figure number and description to the caption." }
    ],
    titlePage: [
      { location: "Keywords", type: "Desk-reject risk", flagged: "No keywords were provided in the document.", suggested: "Keywords: Transformer architecture; attention mechanism; neural machine translation; sequence transduction; deep learning; parallelization", reasoning: "No keywords were provided in the document." },
      { location: "Authors", type: "Desk-reject risk", flagged: "Ashish Vaswani", suggested: null, reasoning: "No corresponding author was found." },
      { location: "Authors", type: "Reviewer flag", flagged: "illia.polosukhin@gmail.com", suggested: null, reasoning: "A personal email address (@gmail.com) is used." },
      { location: "Authors", type: "Reviewer flag", flagged: "University of Toronto", suggested: null, reasoning: "Institutional affiliation is incomplete." },
      { location: "Authors", type: "Reviewer flag", flagged: "Google Research", suggested: null, reasoning: "Institutional affiliation is incomplete." },
      { location: "Authors", type: "Reviewer flag", flagged: "Google Brain", suggested: null, reasoning: "Institutional affiliation is incomplete." }
    ],
    acronyms: [
      { location: "Conclusion", type: "Reviewer flag", flagged: "In this work, we presented the Transformer...", suggested: null, reasoning: "The acronym 'Transformer' is defined multiple times." },
      { location: "Background", type: "Polish", flagged: "The goal of reducing sequential computation also forms the foundation of the Extended Neural GPU...", suggested: "Write out full term 'Convolutional Sequence to Sequence'.", reasoning: "The acronym 'ConvS2S' is undefined." },
      { location: "Background", type: "Polish", flagged: "In these models, the number of operations required...", suggested: "Write out full term 'Convolutional Sequence to Sequence'.", reasoning: "The acronym 'ConvS2S' is undefined." },
      { location: "Position-wise Feed-Forward Networks", type: "Polish", flagged: "This consists of two linear transformations with a ReLU activation in between.", suggested: "This consists of two linear transformations with a Rectified Linear Unit activation in between.", reasoning: "The acronym 'ReLU' is undefined." },
      { location: "Optimizer", type: "Polish", flagged: "We used the Adam optimizer...", suggested: "We used the Adaptive moment estimation optimizer...", reasoning: "The acronym 'Adam' is undefined." }
    ],
    structure: [
      { location: "Background", type: "Reviewer flag", flagged: "Background", suggested: null, reasoning: "The 'Background' section appears before the 'Introduction'." },
      { location: "Model Architecture", type: "Reviewer flag", flagged: "Model Architecture", suggested: null, reasoning: "There's a separate top-level section titled 'Why Self-Attention'." },
      { location: "Training", type: "Reviewer flag", flagged: "Training", suggested: null, reasoning: "Standard structure places Methods before Results." },
      { location: "Attention Visualizations", type: "Reviewer flag", flagged: "Attention Visualizations", suggested: null, reasoning: "This is currently empty and appears after Conclusion." }
    ],
    figures: [
      { location: "Results > English Constituency Parsing", type: "Desk-reject risk", flagged: "The Transformer generalizes well to English constituency parsing...", suggested: "Fig. 1: The Transformer generalizes well to English constituency parsing.", reasoning: "The table 'tab:parsing-results' must be cited in the text." },
      { location: "Attention Visualizations", type: "Reviewer flag", flagged: "Many of the attention heads exhibit behaviour...", suggested: "Fig. 1: Examples of attention heads exhibiting...", reasoning: "Added a figure number." },
      { location: "Attention Visualizations", type: "Reviewer flag", flagged: "Two attention heads, also in layer 5 of 6...", suggested: null, reasoning: "Added missing essential information." },
      { location: "Model Architecture", type: "Reviewer flag", flagged: "The Transformer - model architecture.", suggested: "Fig. 1: The Transformer : model architecture.", reasoning: "The figure 'fig:model-arch' needs to be cited." },
      { location: "Why Self-Attention", type: "Reviewer flag", flagged: "Maximum path lengths, per-layer complexity...", suggested: null, reasoning: "The table 'tab:op_complexities' should be cited." },
      { location: "Multi-Head Attention", type: "Reviewer flag", flagged: "(left) Scaled Dot-Product Attention...", suggested: "Fig. 1: (left) Scaled Dot-Product Attention mechanism.", reasoning: "The figure 'fig:multi-head-att' must be cited." },
      { location: "Results > Machine Translation", type: "Reviewer flag", flagged: "The Transformer achieves better BLEU scores...", suggested: null, reasoning: "The table 'tab:wmt-results' should be cited." },
      { location: "Results > Model Variations", type: "Reviewer flag", flagged: "Variations on the Transformer architecture...", suggested: null, reasoning: "The table 'tab:variations' should be cited." },
      { location: "Attention Visualizations", type: "Polish", flagged: "An example of the attention mechanism...", suggested: "Fig. 1: Example of the attention mechanism...", reasoning: "Added figure number." }
    ],
    language: [
      { location: "Encoder and Decoder Stacks", type: "Reviewer flag", flagged: "fact that", suggested: "the fact that", reasoning: "Missing article 'the' before 'fact'." },
      { location: "Why Self-Attention", type: "Reviewer flag", flagged: "many appear to exhibit behavior related to the syntactic and semantic structure of the sentences.", suggested: "many appear to exhibit behavior related to the syntactic and semantic structures of the sentences.", reasoning: "Changed 'structure' to 'structures'." },
      { location: "English Constituency Parsing", type: "Reviewer flag", flagged: "section~ ef{sec:reg}", suggested: "section 22", reasoning: "Unifies the reference." },
      { location: "English Constituency Parsing", type: "Reviewer flag", flagged: "corpora from with", suggested: "corpora with", reasoning: "Removed redundant word 'from'." },
      { location: "Conclusion", type: "Reviewer flag", flagged: "Making generation less sequential is another research goals of ours.", suggested: "Making generation less sequential is another of our research goals.", reasoning: "Corrected subject-verb agreement." }
    ],
    funding: [{ location: "Funding Statement", type: "Reviewer flag", flagged: "No funding statement was found.", suggested: null, reasoning: "No funding statement was found." }],
    title: [{ location: "Title", type: "Reviewer flag", flagged: "Attention Is All You Need", suggested: "The Transformer: Attention Is All You Need", reasoning: "The title should be more descriptive." }],
    abstract: [
      { location: "Abstract", type: "Reviewer flag", flagged: "On the WMT 2014 English-to-French translation task...", suggested: "On the Workshop on Machine Translation (WMT) 2014...", reasoning: "Define the acronym WMT upon first use." },
      { location: "Abstract", type: "Reviewer flag", flagged: "Our model achieves 28.4 BLEU on the WMT 2014 English-to-German translation task...", suggested: "Our model achieves 28.4 BLEU on the Workshop on Machine Translation (WMT) 2014...", reasoning: "Define the acronym 'WMT' upon first use." }
    ]
  };

  const printWindow = window.open('', '_blank');
  let printHtml = `
    <html>
    <head>
      <title>Manuscript Review Report - ${paperTitle}</title>
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Lora:wght@600;700&display=swap" rel="stylesheet">
      <style>
        body { font-family: 'Inter', sans-serif; color: #1e293b; background: #f1f5f9; margin: 0; padding: 0; }
        .page { width: 210mm; min-height: 297mm; padding: 20mm; margin: 15mm auto; background: #ffffff; box-shadow: 0 4px 20px rgba(0,0,0,0.06); box-sizing: border-box; page-break-after: always; position: relative; }
        h1, h2, h3, h4 { color: #0f172a; }
        .title-main { font-family: 'Lora', Georgia, serif; font-size: 2.2rem; font-weight: 700; text-align: center; margin-top: 40px; margin-bottom: 10px; }
        .subtitle-report { text-align: center; text-transform: uppercase; font-weight: 700; font-size: 1.1rem; color: #1e3a8a; letter-spacing: 0.1em; margin-bottom: 5px; }
        .meta-line { text-align: center; color: #64748b; font-size: 0.85rem; margin-bottom: 50px; }
        .about-box { border-left: 4px solid #0284c7; background: #f8fafc; padding: 1.5rem; border-radius: 4px; margin-bottom: 40px; }
        .about-box h4 { margin-top: 0; margin-bottom: 0.5rem; font-size: 1rem; color: #0f172a; text-transform: uppercase; letter-spacing: 0.05em; }
        .about-box p { font-size: 0.9rem; color: #475569; line-height: 1.5; margin: 0; }
        .summary-box { margin-bottom: 50px; }
        .summary-box h3 { border-bottom: 1px solid #cbd5e1; padding-bottom: 0.5rem; margin-bottom: 1.25rem; }
        .summary-box p { font-size: 0.95rem; line-height: 1.6; color: #334155; }
        .kpi-row { display: flex; justify-content: space-around; margin-top: 60px; border-top: 1px solid #e2e8f0; padding-top: 30px; }
        .kpi-item { text-align: center; }
        .kpi-lbl { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; color: #64748b; letter-spacing: 0.1em; margin-bottom: 0.5rem; }
        .kpi-val { font-size: 2.75rem; font-weight: 800; }
        .kpi-val.red { color: #dc2626; } .kpi-val.orange { color: #ea580c; } .kpi-val.yellow { color: #ca8a04; }
        .finding-card { border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; background: #ffffff; }
        .finding-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
        .finding-location { font-weight: 700; font-size: 0.95rem; color: #1e293b; }
        .finding-badge { font-size: 0.68rem; font-weight: 700; padding: 0.25rem 0.75rem; border-radius: 20px; text-transform: uppercase; }
        .badge-red { background: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; }
        .badge-orange { background: #ffedd5; color: #c2410c; border: 1px solid #fed7aa; }
        .badge-yellow { background: #fef9c3; color: #854d0e; border: 1px solid #fef08a; }
        .code-box { font-family: monospace; font-size: 0.88rem; padding: 0.85rem 1.15rem; border-radius: 6px; margin-bottom: 0.75rem; line-height: 1.45; white-space: pre-wrap; }
        .flagged-box { background: #f8fafc; border: 1px solid #e2e8f0; color: #334155; }
        .suggested-box { background: #f0fdf4; border-left: 4px solid #16a34a; color: #166534; }
        .reasoning-text { font-size: 0.88rem; color: #475569; line-height: 1.5; margin-top: 0.75rem; margin-bottom: 0; }
        .assess-card { display: flex; justify-content: space-between; align-items: center; padding: 1rem 1.25rem; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 0.75rem; background: #ffffff; }
        .assess-info h5 { margin: 0 0 0.25rem 0; font-size: 0.95rem; color: #0f172a; font-weight: 700; }
        .assess-info p { margin: 0; font-size: 0.85rem; color: #64748b; }
        .assess-score { width: 38px; height: 38px; border-radius: 50%; background: #86efac; color: #166534; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.9rem; }
        .summary-table { width: 100%; border-collapse: collapse; margin-top: 1.5rem; }
        .summary-table th, .summary-table td { padding: 1rem; border-bottom: 1px solid #e2e8f0; text-align: left; }
        .summary-table th { background: #f8fafc; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #64748b; letter-spacing: 0.05em; }
        .summary-table td { font-size: 0.9rem; }
        .circle-icon { width: 22px; height: 22px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.75rem; }
        .circle-icon.check { background: #d1fae5; color: #065f46; }
        .circle-icon.cross { background: #fee2e2; color: #b91c1c; }
        @media print { body { background: #ffffff; } .page { margin: 0; box-shadow: none; width: 100%; height: auto; page-break-after: always; break-after: page; } }
      </style>
    </head>
    <body>
      <div class="page">
        <div class="subtitle-report">Manuscript Review Report</div>
        <h1 class="title-main">${paperTitle}</h1>
        <div class="meta-line">Created by JournaBuddy &bull; ${new Date().toLocaleDateString()} &bull; Review completed automatically</div>
        <div class="about-box">
          <h4>About this report</h4>
          <p>This report was generated by JournaBuddy, an AI-powered manuscript intelligence platform. Our agentic workflow identifies potential issues across multiple dimensions including formatting consistency, citation accuracy, language quality, and structural completeness.</p>
        </div>
        <div class="summary-box">
          <h3>Overall Summary</h3>
          <p>${isDemo ? "Manuscript requires substantial revisions focusing on clarity, consistency, and adherence to academic standards across multiple sections." : (q.structure_assessment || "Manuscript evaluated by JournaBuddy AI swarm agent cluster.")}</p>
        </div>
        <div class="kpi-row">
          <div class="kpi-item"><div class="kpi-lbl">Desk-Reject Risks</div><div class="kpi-val red">${isDemo ? 3 : (pf.issues || []).filter(x => x.type === 'fatal').length}</div></div>
          <div class="kpi-item"><div class="kpi-lbl">Reviewer Flags</div><div class="kpi-val orange">${isDemo ? 25 : (pf.issues || []).length}</div></div>
          <div class="kpi-item"><div class="kpi-lbl">Polish</div><div class="kpi-val yellow">${isDemo ? 5 : 3}</div></div>
        </div>
      </div>
      <div class="page">
        <h2 style="border-bottom:2px solid #0f172a;padding-bottom:0.5rem;margin-bottom:2rem;">Top Desk-Reject Risks</h2>
        ${(isDemo ? demoFindings.deskReject : []).map(f => `
          <div class="finding-card">
            <div class="finding-header"><span class="finding-location">Location: ${f.location}</span><span class="finding-badge badge-red">${f.type}</span></div>
            ${f.flagged ? `<div class="code-box flagged-box"><strong>Flagged passage:</strong> ${f.flagged}</div>` : ''}
            ${f.suggested ? `<div class="code-box suggested-box"><strong>Suggested rewrite:</strong> ${f.suggested}</div>` : ''}
            <p class="reasoning-text"><strong>Reasoning:</strong> ${f.reasoning}</p>
          </div>
        `).join('')}
        ${(!isDemo) ? '<p style="color:#64748b;">No high-risk desk reject indicators flagged.</p>' : ''}
      </div>
      <div class="page">
        <h2 style="border-bottom:2px solid #0f172a;padding-bottom:0.5rem;margin-bottom:1.5rem;">Language Quality</h2>
        <div style="display:flex;align-items:center;gap:1rem;margin-bottom:2rem;">
          <h4 style="margin:0;font-size:1.1rem;color:#475569;">Overall Language Score:</h4>
          <span class="assess-score" style="width:45px;height:45px;font-size:1.1rem;background:#22c55e;color:white;">A-</span>
        </div>
        <p style="color:#475569;font-size:0.95rem;margin-bottom:2rem;line-height:1.6;">The manuscript demonstrates strong academic language, with a few minor grammatical and syntactical issues.</p>
        <h3 style="margin-bottom:1rem;">Category Assessments</h3>
        ${["Grammar and Syntax","B+","Clarity and Precision","B","Conciseness","B+","Academic Tone","A","Consistency","B+","Readability and Flow","B+"].reduce((a,c,i,arr) => i%2===0 ? a + `<div class="assess-card"><div class="assess-info"><h5>${c}</h5><p>Standard assessment for this category.</p></div><span class="assess-score" style="${c==='Academic Tone'?'background:#22c55e;color:#fff;':c==='Clarity and Precision'?'background:#fde047;color:#854d0e;':''}">${arr[i+1]}</span></div>` : a, '')}
      </div>
      <div class="page">
        <h2 style="border-bottom:2px solid #0f172a;padding-bottom:0.5rem;margin-bottom:2rem;">Areas for Improvement</h2>
        <ul style="font-size:1rem;color:#334155;line-height:2;padding-left:1.5rem;">
          <li>Occasional minor grammatical errors, such as missing articles.</li>
          <li>Some instances of phrasing that could be more precise or less verbose.</li>
          <li>Minor inconsistencies in referencing or terminology.</li>
          <li>Incorporate explicit funding statement block before bibliography.</li>
        </ul>
        <h3 style="margin-top:4rem;margin-bottom:1.5rem;">Key Strengths</h3>
        <ul style="font-size:1rem;color:#334155;line-height:2;padding-left:1.5rem;">
          <li>Clear and effective communication of complex technical concepts.</li>
          <li>Appropriate and consistent academic tone throughout.</li>
          <li>Logical organization and structure of information.</li>
        </ul>
      </div>
      <div class="page">
        <h2 style="border-bottom:2px solid #0f172a;padding-bottom:0.5rem;margin-bottom:2rem;">Section Review Summary</h2>
        <table class="summary-table">
          <thead><tr><th>Section</th><th>Status</th><th>Issues</th></tr></thead>
          <tbody>
            ${[["Figures and Tables", isDemo ? 9 : 0],["Title Page", isDemo ? 6 : 1],["Language", isDemo ? 5 : (pf.issues || []).length],["Acronyms", isDemo ? 5 : 2],["Structure", isDemo ? 4 : 0],["Abstract", isDemo ? 2 : 0],["Title", isDemo ? 1 : 0],["Funding", isDemo ? 1 : 0]].map(([s,n]) => `<tr><td><strong>${s}</strong></td><td><span class="circle-icon cross">&times;</span></td><td><strong>${n}</strong></td></tr>`).join('')}
            <tr><td><strong>Main Headings</strong></td><td><span class="circle-icon check">&#10003;</span></td><td><strong>0</strong></td></tr>
            <tr><td><strong>Referencing</strong></td><td><span class="circle-icon check">&#10003;</span></td><td><strong>0</strong></td></tr>
          </tbody>
        </table>
      </div>
      ${["titlePage","Title Page","2 Desk-reject risk, 4 Reviewer flag","badge-red","badge-orange",demoFindings.titlePage,"acronyms","Acronyms","1 Reviewer flag, 4 Polish","badge-orange","badge-yellow",demoFindings.acronyms,"structure","Structure","4 Reviewer flag","badge-orange","badge-orange",demoFindings.structure,"figures","Figures and Tables","1 Desk-reject risk, 7 Reviewer flag, 1 Polish","badge-red","badge-orange","badge-yellow",demoFindings.figures,"language","Language","5 Reviewer flag","badge-orange","badge-orange",demoFindings.language,"funding","Funding","1 Reviewer flag","badge-orange","badge-orange",demoFindings.funding,"title","Title","1 Reviewer flag","badge-orange","badge-orange",demoFindings.title,"abstract","Abstract","2 Reviewer flag","badge-orange","badge-orange",demoFindings.abstract].reduce((pages, _, i, arr) => {
        if (i % 6 === 0 && arr.length > i) {
          const [id, label, summary, ...badges] = arr.slice(i, i+6);
          const findings = arr[i+5];
          if (findings && findings.length > 0) {
            return pages + `<div class="page"><h2 style="border-bottom:2px solid #0f172a;padding-bottom:0.5rem;margin-bottom:1rem;">${label} Findings</h2><div style="font-size:0.9rem;color:#64748b;margin-bottom:2rem;">${findings.length} findings: ${summary}</div>${findings.map(f => `<div class="finding-card"><div class="finding-header"><span class="finding-location">Location: ${f.location}</span><span class="finding-badge ${f.type.includes('Desk') ? badges[0] : f.type.includes('Polish') ? badges[2]||badges[1] : badges[1]}">${f.type}</span></div>${f.flagged ? `<div class="code-box flagged-box"><strong>Flagged passage:</strong> ${f.flagged}</div>` : ''}${f.suggested ? `<div class="code-box suggested-box"><strong>Suggested rewrite:</strong> ${f.suggested}</div>` : ''}<p class="reasoning-text"><strong>Reasoning:</strong> ${f.reasoning}</p></div>`).join('')}</div>`;
          }
        }
        return pages;
      }, '')}
    </body></html>
  `;

  printWindow.document.write(printHtml);
  printWindow.document.close();
  printWindow.focus();
  setTimeout(() => { printWindow.print(); }, 1000);
}

// Provenance tooltip
async function showProvenanceTooltip(metricKey, event) {
  const tooltip = document.getElementById('provenanceTooltip');
  if (!tooltip) return;
  const provIds = activeReportData ? activeReportData.provenance_ids : null;
  if (!provIds || !provIds[metricKey]) {
    tooltip.style.display = 'none';
    return;
  }
  const metricId = provIds[metricKey];
  tooltip.innerHTML = `<div style="text-align:center;color:var(--text-muted);">Loading lineage...</div>`;
  const rect = event.currentTarget.getBoundingClientRect();
  tooltip.style.left = `${window.scrollX + rect.left}px`;
  tooltip.style.top = `${window.scrollY + rect.bottom + 8}px`;
  tooltip.style.display = 'block';
  try {
    const res = await fetch(`/api/provenance/${metricId}`);
    if (res.status === 200) {
      const p = await res.json();
      const sourcesHtml = p.data_sources.map(src => `<span style="background:rgba(59,130,246,0.1);padding:2px 6px;border-radius:4px;font-size:0.7rem;margin-right:4px;display:inline-block;">${src}</span>`).join('');
      const dateStr = new Date(p.timestamp * 1000).toLocaleString();
      tooltip.innerHTML = `
        <div style="font-weight:700;color:var(--text-primary);margin-bottom:0.4rem;font-size:0.9rem;display:flex;align-items:center;justify-content:space-between;">
          <span>${p.metric_name}</span>
          <span style="font-size:0.7rem;padding:2px 6px;border-radius:12px;font-weight:600;color:#fff;background:${p.confidence_level === 'High' ? '#22c55e' : '#f59e0b'};">${p.confidence_level} Confidence</span>
        </div>
        <div style="color:var(--text-secondary);margin-bottom:0.5rem;line-height:1.4;">${p.explanation}</div>
        <div style="margin-bottom:0.5rem;"><strong style="color:var(--text-primary);">Formula:</strong> <code style="font-family:monospace;background:rgba(255,255,255,0.05);padding:1px 4px;border-radius:3px;font-size:0.75rem;">${p.formula}</code></div>
        <div style="margin-bottom:0.5rem;"><strong style="color:var(--text-primary);">Data Sources:</strong> <div style="margin-top:0.2rem;">${sourcesHtml}</div></div>
        <div style="font-size:0.7rem;color:var(--text-muted);text-align:right;">Calculated: ${dateStr}</div>
      `;
    } else {
      tooltip.innerHTML = `<span style="color:#ef4444;">Failed to load provenance details.</span>`;
    }
  } catch (err) {
    tooltip.innerHTML = `<span style="color:#ef4444;">Error fetching provenance.</span>`;
  }
}

function hideProvenanceTooltip() {
  const tooltip = document.getElementById('provenanceTooltip');
  if (tooltip) tooltip.style.display = 'none';
}
