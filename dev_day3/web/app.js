// ── Mini ASM — app.js ──────────────────────────────────────────────────────
const API = window.location.port === '5500'   // live-server dev
  ? 'http://127.0.0.1:8080'
  : window.location.origin;

// ── State ──────────────────────────────────────────────────────────────────
let allAssets = [];           // [{id,name,type,status,created_at}, …]
let allJobs   = [];           // [{id,asset_id,scan_type,status,…}, …]
let selectedScanType = 'dns';
let currentResultFilter = 'all';

const SCAN_TYPES = [
  { key:'dns',       label:'DNS Scanning',            badge:'passive', icon:'fa-server' },
  { key:'whois',     label:'WHOIS Lookup',             badge:'passive', icon:'fa-address-card' },
  { key:'subdomain', label:'Subdomain Enumeration',    badge:'passive', icon:'fa-sitemap' },
  { key:'ssl',       label:'SSL/TLS Probing',          badge:'active',  icon:'fa-lock' },
  { key:'tech',      label:'Tech Fingerprinting',      badge:'passive', icon:'fa-microchip' },
  { key:'ip',        label:'IP GeoIP & ASN',           badge:'passive', icon:'fa-globe' },
  { key:'port',      label:'Port Scanning',            badge:'active',  icon:'fa-network-wired' },
  { key:'cve',       label:'CVE Correlation',          badge:'active',  icon:'fa-bug' },
  { key:'all',       label:'All Passive Scans',        badge:'passive', icon:'fa-layer-group' },
];

// ── Navigation ─────────────────────────────────────────────────────────────
document.querySelectorAll('.nav-link[data-page]').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-link').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('page-' + btn.dataset.page).classList.add('active');
    if (btn.dataset.page === 'scanning') populateScanPanel();
    if (btn.dataset.page === 'results')  renderResults();
    if (btn.dataset.page === 'dashboard') refreshStats();
  });
});

// ── Bootstrap ──────────────────────────────────────────────────────────────
async function init() {
  buildScanTypeList();
  await fetchAssets();
  await loadAllJobs();
  refreshStats();
  populateScanPanel();
  // Poll active jobs every 4 s
  setInterval(async () => {
    const hasPending = allJobs.some(j => j.status === 'pending' || j.status === 'running');
    if (hasPending) { await loadAllJobs(); renderResults(); refreshStats(); }
  }, 4000);
}

// ── Data fetching ──────────────────────────────────────────────────────────
async function fetchAssets() {
  try {
    const r = await fetch(`${API}/assets`);
    allAssets = await r.json();
    renderAssetsTable();
    populateScanPanel();
  } catch(e) { console.error('fetchAssets:', e); }
}

async function loadAllJobs() {
  // Collect jobs for every asset
  try {
    const jobMap = {};
    await Promise.all(allAssets.map(async a => {
      const r = await fetch(`${API}/assets/${a.id}/scans`);
      const jobs = await r.json();
      jobs.forEach(j => { jobMap[j.id] = { ...j, _assetName: a.name, _assetType: a.type }; });
    }));
    allJobs = Object.values(jobMap).sort((a,b) => b.created_at.localeCompare(a.created_at));
    renderJobQueue();
  } catch(e) { console.error('loadAllJobs:', e); }
}

// ── Dashboard stats ────────────────────────────────────────────────────────
function refreshStats() {
  const total     = allAssets.length;
  const active    = allAssets.filter(a => a.status === 'active').length;
  const totalJobs = allJobs.length;
  const completed = allJobs.filter(j => j.status === 'completed').length;
  document.getElementById('stat-total').textContent     = total;
  document.getElementById('stat-active').textContent    = active;
  document.getElementById('stat-active-sub').textContent = `${active} active`;
  document.getElementById('stat-scans').textContent     = totalJobs;
  document.getElementById('stat-completed').textContent = completed;
}

// ── Assets table ───────────────────────────────────────────────────────────
function renderAssetsTable() {
  const q    = (document.getElementById('assetSearch')?.value || '').toLowerCase();
  const type = document.getElementById('assetFilterType')?.value || '';
  const filtered = allAssets.filter(a =>
    (!q    || a.name.toLowerCase().includes(q)) &&
    (!type || a.type === type)
  );
  const tbody = document.getElementById('assets-tbody');
  if (!filtered.length) {
    tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state">
      <i class="fa-solid fa-database"></i><p>No assets found.</p></div></td></tr>`;
    return;
  }
  tbody.innerHTML = filtered.map(a => {
    const jobCount = allJobs.filter(j => j.asset_id === a.id).length;
    const typeIcon = a.type === 'domain'
      ? '<span class="type-icon type-domain"><i class="fa-solid fa-globe"></i></span>'
      : '<span class="type-icon type-ip"><i class="fa-solid fa-server"></i></span>';
    const date = a.created_at ? a.created_at.split('T')[0] : '—';
    return `<tr>
      <td>${typeIcon}<strong>${esc(a.name)}</strong></td>
      <td><span class="badge badge-${a.type==='domain'?'blue':'gray'}">${a.type.toUpperCase()}</span></td>
      <td><span class="badge badge-green">${a.status || 'active'}</span></td>
      <td style="color:var(--muted)">${date}</td>
      <td><span class="badge badge-gray">${jobCount}</span></td>
      <td>
        <button class="btn-danger-sm" onclick="deleteAsset('${a.id}')">
          <i class="fa-solid fa-trash"></i> Delete
        </button>
      </td>
    </tr>`;
  }).join('');
}

// ── Add Asset modal ────────────────────────────────────────────────────────
function openAddModal() {
  document.getElementById('addModal').classList.add('open');
  document.getElementById('modalAssetName').focus();
}
function closeAddModal() {
  document.getElementById('addModal').classList.remove('open');
  document.getElementById('modalAssetName').value = '';
}
document.getElementById('addModal').addEventListener('click', e => {
  if (e.target === document.getElementById('addModal')) closeAddModal();
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeAddModal();
  if (e.key === 'Enter' && document.getElementById('addModal').classList.contains('open'))
    submitAddAsset();
});

async function submitAddAsset() {
  const name = document.getElementById('modalAssetName').value.trim();
  const type = document.getElementById('modalAssetType').value;
  if (!name) { alert('Asset name cannot be empty.'); return; }
  try {
    const r = await fetch(`${API}/assets`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ name, type })
    });
    const data = await r.json();
    if (!r.ok) { alert('Error: ' + data.error); return; }
    closeAddModal();
    await fetchAssets();
    refreshStats();
  } catch(e) { alert('Failed: ' + e.message); }
}

async function deleteAsset(id) {
  if (!confirm('Delete this asset and all its scan data?')) return;
  try {
    const r = await fetch(`${API}/assets/${id}`, { method:'DELETE' });
    if (!r.ok) { const d = await r.json(); alert(d.error); return; }
    allJobs = allJobs.filter(j => j.asset_id !== id);
    await fetchAssets();
    refreshStats();
    renderResults();
  } catch(e) { alert('Failed: ' + e.message); }
}

// ── Scan type selector ─────────────────────────────────────────────────────
function buildScanTypeList() {
  const el = document.getElementById('scanTypeList');
  el.innerHTML = SCAN_TYPES.map(t => `
    <div class="scan-type-item ${t.key===selectedScanType?'selected':''}"
         onclick="selectScanType('${t.key}')">
      <span><i class="fa-solid ${t.icon}" style="width:16px;margin-right:6px;color:var(--muted)"></i>${t.label}</span>
      <span class="badge ${t.badge==='passive'?'badge-green':'badge-orange'}">${t.badge}</span>
    </div>`).join('');
}

function selectScanType(key) {
  selectedScanType = key;
  buildScanTypeList();
}

function populateScanPanel() {
  const sel = document.getElementById('scanAssetSelect');
  if (!sel) return;
  const prev = sel.value;
  sel.innerHTML = '<option value="">— Select asset —</option>' +
    allAssets.map(a => `<option value="${a.id}" ${a.id===prev?'selected':''}>${esc(a.name)} [${a.type.toUpperCase()}]</option>`).join('');
}

async function dispatchScan() {
  const assetId = document.getElementById('scanAssetSelect').value;
  if (!assetId) { alert('Please select an asset first.'); return; }
  try {
    const r = await fetch(`${API}/assets/${assetId}/scan`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ scan_type: selectedScanType })
    });
    const job = await r.json();
    if (!r.ok) { alert('Error: ' + job.error); return; }
    await loadAllJobs();
    refreshStats();
  } catch(e) { alert('Failed: ' + e.message); }
}

// ── Job queue render ───────────────────────────────────────────────────────
function renderJobQueue() {
  const el = document.getElementById('jobQueue');
  if (!allJobs.length) {
    el.innerHTML = '<div class="empty-state"><i class="fa-solid fa-wave-square"></i><p>No scan jobs yet.</p></div>';
    return;
  }
  const statusIcon = { pending:'fa-clock', running:'fa-spinner fa-spin', completed:'fa-circle-check', failed:'fa-circle-xmark', partial:'fa-triangle-exclamation' };
  const statusColor = { pending:'var(--muted)', running:'var(--accent)', completed:'var(--green)', failed:'var(--red)', partial:'var(--orange)' };
  const iconBg = { pending:'#f1f5f9', running:'#eff6ff', completed:'#d1fae5', failed:'#fee2e2', partial:'#fff7ed' };

  el.innerHTML = allJobs.slice(0, 30).map(j => {
    const st = j.status || 'pending';
    return `<div class="queue-item">
      <div class="queue-icon" style="background:${iconBg[st]};color:${statusColor[st]}">
        <i class="fa-solid ${statusIcon[st]}"></i>
      </div>
      <div class="queue-info">
        <div class="qname">${esc(j._assetName || '—')}</div>
        <div class="qmeta">${j.scan_type?.toUpperCase()} · ${j.created_at?.split('T')[0] || ''}</div>
      </div>
      <span class="badge ${badgeClass(st)}">${st}</span>
    </div>`;
  }).join('');
}

function badgeClass(st) {
  return { pending:'badge-gray', running:'badge-blue', completed:'badge-green', failed:'badge-red', partial:'badge-orange' }[st] || 'badge-gray';
}

// ── Results render ─────────────────────────────────────────────────────────
document.getElementById('resultsFilter').addEventListener('click', e => {
  const btn = e.target.closest('.filter-btn');
  if (!btn) return;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentResultFilter = btn.dataset.filter;
  renderResults();
});

async function renderResults() {
  const container = document.getElementById('resultsContainer');
  const completed = allJobs.filter(j =>
    j.status === 'completed' &&
    (currentResultFilter === 'all' || j.scan_type === currentResultFilter)
  );
  if (!completed.length) {
    container.innerHTML = '<div class="empty-state"><i class="fa-solid fa-file-lines"></i><p>No completed results for this filter.</p></div>';
    return;
  }
  // Fetch results for jobs we don't have yet
  const cards = await Promise.all(completed.slice(0, 20).map(async j => {
    let results = j._results;
    if (!results) {
      try {
        const r = await fetch(`${API}/scan-jobs/${j.id}/results`);
        const d = await r.json();
        results = d.results;
        j._results = results;
      } catch { results = []; }
    }
    return buildResultCard(j, results);
  }));
  container.innerHTML = cards.join('');
}

function buildResultCard(job, results) {
  const typeLabel = (SCAN_TYPES.find(t=>t.key===job.scan_type)||{label:job.scan_type}).label;
  const date = job.ended_at ? job.ended_at.replace('T',' ').substring(0,16) : '';
  const body = renderResultBody(job.scan_type, results);
  return `<div class="result-card">
    <div class="result-card-header" onclick="this.nextElementSibling.style.display=this.nextElementSibling.style.display==='none'?'block':'none'">
      <div class="rh-left">
        <span class="badge ${badgeClass('completed')}"><i class="fa-solid fa-circle-check"></i></span>
        <strong>${esc(job._assetName || '—')}</strong>
        <span class="badge badge-gray">${typeLabel}</span>
      </div>
      <span style="font-size:12px;color:var(--muted)">${date} <i class="fa-solid fa-chevron-down" style="margin-left:6px"></i></span>
    </div>
    <div class="result-card-body">${body}</div>
  </div>`;
}

function renderResultBody(scanType, results) {
  if (!results || !results.length) return '<span style="color:var(--muted)">No data returned.</span>';
  const r = results[0];
  if (!r) return '<span style="color:var(--muted)">Empty result.</span>';

  if (scanType === 'dns' && r.records) {
    const rows = Object.entries(r.records)
      .filter(([,v]) => v && v.length)
      .map(([k,v]) => `<div class="result-row"><span class="result-key">${k}</span><span class="result-val">${v.slice(0,5).join(', ')}</span></div>`);
    return rows.length ? rows.join('') : '<span style="color:var(--muted)">No DNS records found.</span>';
  }

  if (scanType === 'whois') {
    return ['registrar','creation_date','expiry_date','status'].map(k =>
      r[k] && r[k] !== 'N/A' ? `<div class="result-row"><span class="result-key">${k.replace('_',' ')}</span><span class="result-val">${esc(r[k])}</span></div>` : ''
    ).join('') || `<pre class="result-pre">${esc((r.raw||'').substring(0,400))}</pre>`;
  }

  if (scanType === 'ssl' && r.certificate) {
    const c = r.certificate;
    const days = c.days_until_expiry;
    const expiryColor = days < 30 ? 'var(--red)' : days < 90 ? 'var(--orange)' : 'var(--green)';
    return `
      <div class="result-row"><span class="result-key">Subject</span><span class="result-val">${esc(c.subject)}</span></div>
      <div class="result-row"><span class="result-key">Issuer</span><span class="result-val">${esc(c.issuer)}</span></div>
      <div class="result-row"><span class="result-key">Valid Until</span><span class="result-val">${esc(c.valid_until)}</span></div>
      <div class="result-row"><span class="result-key">Days Left</span><span class="result-val" style="color:${expiryColor};font-weight:600">${days}</span></div>
      <div class="result-row"><span class="result-key">TLS Version</span><span class="result-val">${esc(r.connection?.tls_version||'—')}</span></div>
      <div class="result-row"><span class="result-key">Grade</span><span class="result-val"><span class="badge badge-green">${r.grade||'A'}</span></span></div>`;
  }

  if (scanType === 'port') {
    const ports = r.open_ports || [];
    if (!ports.length) return '<span style="color:var(--green)"><i class="fa-solid fa-shield-halved"></i> No open ports found</span>';
    return ports.map(p =>
      `<div class="result-row">
        <span class="result-key"><span class="badge badge-red">PORT ${p.port}</span></span>
        <span class="result-val"><strong>${p.service?.toUpperCase()}</strong> / ${p.protocol} — ${esc(p.version||'')}</span>
      </div>`).join('') +
      `<div style="margin-top:8px;font-size:12px;color:var(--muted)">Scanned ${r.total_scanned} ports in ${r.scan_duration_ms}ms</div>`;
  }

  if (scanType === 'tech' && r.technologies) {
    return r.technologies.map(t =>
      `<div class="result-row">
        <span class="result-key"><span class="badge badge-gray">${esc(t.category)}</span></span>
        <span class="result-val"><strong>${esc(t.name)}</strong>${t.version ? ' v'+esc(t.version) : ''} <span style="color:var(--muted);font-size:12px">(${t.confidence}% confidence)</span></span>
      </div>`).join('');
  }

  if (scanType === 'ip' && r.geolocation) {
    const g = r.geolocation, a = r.asn || {};
    return `
      <div class="result-row"><span class="result-key">IP</span><span class="result-val">${esc(r.ip_address)}</span></div>
      <div class="result-row"><span class="result-key">Location</span><span class="result-val">${esc(g.city||'')}, ${esc(g.country||'')}</span></div>
      <div class="result-row"><span class="result-key">ISP</span><span class="result-val">${esc(g.isp||'—')}</span></div>
      <div class="result-row"><span class="result-key">ASN</span><span class="result-val">AS${a.number} — ${esc(a.description||'')}</span></div>
      <div class="result-row"><span class="result-key">Reverse DNS</span><span class="result-val">${esc(r.reverse_dns||'—')}</span></div>`;
  }

  if (scanType === 'cve' && r.cve_findings) {
    if (!r.cve_findings.length) return '<span style="color:var(--green)"><i class="fa-solid fa-shield-halved"></i> No CVEs found</span>';
    return r.cve_findings.flatMap(f => f.cves.map(c => {
      const bc = c.severity==='CRITICAL'?'badge-red':c.severity==='HIGH'?'badge-orange':'badge-gray';
      return `<div class="result-row">
        <span class="result-key"><span class="badge ${bc}">${c.severity}</span></span>
        <span class="result-val"><strong>${esc(c.cve_id)}</strong> (${esc(f.service)}:${f.port}) — ${esc(c.description)}</span>
      </div>`;
    })).join('');
  }

  if (scanType === 'subdomain' && r.subdomains) {
    if (!r.subdomains.length) return '<span style="color:var(--muted)">No subdomains found.</span>';
    return `<div class="result-row"><span class="result-key">Found</span><span class="result-val">${r.subdomains.length} subdomains</span></div>` +
      r.subdomains.slice(0,20).map(s =>
        `<div class="result-row"><span class="result-key"></span><span class="result-val">${esc(s)}</span></div>`).join('');
  }

  // fallback
  return `<pre class="result-pre">${esc(JSON.stringify(r, null, 2).substring(0,600))}</pre>`;
}

// ── Helpers ────────────────────────────────────────────────────────────────
function esc(s) {
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── Start ──────────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', init);