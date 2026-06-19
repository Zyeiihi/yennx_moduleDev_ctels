const API = (window.location.port === '5500' || window.location.port === '3000')
  ? 'http://127.0.0.1:8080'
  : window.location.origin;

let allAssets = [];
let allJobs   = [];
let selectedScanType = 'dns';
let resultFilter = 'all';

const SCAN_TYPES = [
  { key:'dns',       label:'DNS scanning',          kind:'passive', icon:'fa-server' },
  { key:'whois',     label:'WHOIS lookup',           kind:'passive', icon:'fa-address-card' },
  { key:'subdomain', label:'Subdomain enumeration',  kind:'passive', icon:'fa-sitemap' },
  { key:'ssl',       label:'SSL / TLS probing',      kind:'active',  icon:'fa-lock' },
  { key:'tech',      label:'Tech fingerprinting',    kind:'passive', icon:'fa-microchip' },
  { key:'ip',        label:'GeoIP & ASN lookup',     kind:'passive', icon:'fa-globe' },
  { key:'port',      label:'Port scanning',          kind:'active',  icon:'fa-network-wired' },
  { key:'cve',       label:'CVE correlation',        kind:'active',  icon:'fa-bug' },
  { key:'all',       label:'All passive scans',      kind:'passive', icon:'fa-layer-group' },
];

const STATUS_BADGE = {
  pending:   'badge-gray',
  running:   'badge-blue',
  completed: 'badge-green',
  failed:    'badge-red',
  partial:   'badge-yellow',
};

// ── Navigation ─────────────────────────────────────────────────────────────
function navigateTo(page) {
  document.querySelectorAll('.nav-item[data-page]').forEach(b => {
    b.classList.toggle('active', b.dataset.page === page);
  });
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.topbar').forEach(t => t.style.display = 'none');
  document.getElementById('page-' + page).classList.add('active');
  document.getElementById('topbar-' + page).style.display = 'flex';
  if (page === 'scanning') populateScanPanel();
  if (page === 'results')  renderResults();
  if (page === 'dashboard') refreshStats();
}

document.querySelectorAll('.nav-item[data-page]').forEach(btn => {
  btn.addEventListener('click', () => navigateTo(btn.dataset.page));
});

// ── Bootstrap ───────────────────────────────────────────────────────────────
async function init() {
  buildScanTypeList();
  await fetchAssets();
  await loadAllJobs();
  refreshStats();
  populateScanPanel();
  setInterval(async () => {
    if (allJobs.some(j => j.status === 'pending' || j.status === 'running')) {
      await loadAllJobs();
      renderResults();
      refreshStats();
    }
  }, 4000);
}

// ── Data ────────────────────────────────────────────────────────────────────
async function fetchAssets() {
  try {
    const r = await fetch(`${API}/assets`);
    allAssets = await r.json();
    renderAssetsTable();
    populateScanPanel();
    document.getElementById('nav-asset-count').textContent = allAssets.length;
  } catch(e) { console.error('fetchAssets:', e); }
}

async function loadAllJobs() {
  try {
    const jobMap = {};
    await Promise.all(allAssets.map(async a => {
      const r = await fetch(`${API}/assets/${a.id}/scans`);
      const jobs = await r.json();
      jobs.forEach(j => { jobMap[j.id] = { ...j, _asset: a }; });
    }));
    allJobs = Object.values(jobMap).sort((a, b) => b.created_at.localeCompare(a.created_at));
    renderJobTable();
    document.getElementById('nav-job-count').textContent = allJobs.length;
  } catch(e) { console.error('loadAllJobs:', e); }
}

// ── Stats ───────────────────────────────────────────────────────────────────
function refreshStats() {
  document.getElementById('stat-total').textContent     = allAssets.length;
  document.getElementById('stat-active').textContent    = allAssets.filter(a => a.status === 'active').length;
  document.getElementById('stat-scans').textContent     = allJobs.length;
  document.getElementById('stat-completed').textContent = allJobs.filter(j => j.status === 'completed').length;
}

// ── Assets table ─────────────────────────────────────────────────────────────
function renderAssetsTable() {
  const q    = (document.getElementById('assetSearch')?.value || '').toLowerCase();
  const type = document.getElementById('assetFilterType')?.value || '';
  const list = allAssets.filter(a =>
    (!q    || a.name.toLowerCase().includes(q)) &&
    (!type || a.type === type)
  );
  const tbody = document.getElementById('assets-tbody');
  if (!list.length) {
    tbody.innerHTML = `<tr><td colspan="6"><div class="empty"><i class="fa-solid fa-database"></i>No assets found.</div></td></tr>`;
    return;
  }
  tbody.innerHTML = list.map(a => {
    const jCount = allJobs.filter(j => j.asset_id === a.id).length;
    const date   = (a.created_at || '').split('T')[0];
    const typeBadge = a.type === 'domain' ? 'badge-blue' : 'badge-purple';
    return `<tr>
      <td style="font-weight:500">${esc(a.name)}</td>
      <td><span class="badge ${typeBadge}">${a.type}</span></td>
      <td><span class="badge badge-green">${a.status || 'active'}</span></td>
      <td style="color:var(--text-muted)">${date}</td>
      <td style="color:var(--text-muted)">${jCount}</td>
      <td style="text-align:right">
        <button class="btn btn-danger" style="padding:3px 8px;font-size:11px" onclick="deleteAsset('${a.id}')">
          <i class="fa-solid fa-trash"></i>
        </button>
      </td>
    </tr>`;
  }).join('');
}

// ── Modal ──────────────────────────────────────────────────────────────────
function openAddModal() { document.getElementById('addModal').classList.add('open'); setTimeout(() => document.getElementById('modalAssetName').focus(), 50); }
function closeAddModal() { document.getElementById('addModal').classList.remove('open'); document.getElementById('modalAssetName').value = ''; }
document.getElementById('addModal').addEventListener('click', e => { if (e.target === document.getElementById('addModal')) closeAddModal(); });
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeAddModal();
  if (e.key === 'Enter' && document.getElementById('addModal').classList.contains('open')) submitAddAsset();
});

async function submitAddAsset() {
  const name = document.getElementById('modalAssetName').value.trim();
  const type = document.getElementById('modalAssetType').value;
  if (!name) return;
  try {
    const r = await fetch(`${API}/assets`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, type }),
    });
    const d = await r.json();
    if (!r.ok) { alert(d.error); return; }
    closeAddModal();
    await fetchAssets(); refreshStats();
  } catch(e) { alert(e.message); }
}

async function deleteAsset(id) {
  if (!confirm('Delete this asset and all its scan data?')) return;
  try {
    await fetch(`${API}/assets/${id}`, { method: 'DELETE' });
    allJobs = allJobs.filter(j => j.asset_id !== id);
    await fetchAssets(); refreshStats(); renderResults();
  } catch(e) { alert(e.message); }
}

// ── Scan config ────────────────────────────────────────────────────────────
function buildScanTypeList() {
  document.getElementById('scanTypeList').innerHTML = SCAN_TYPES.map(t => `
    <div class="scan-type-option ${t.key === selectedScanType ? 'selected' : ''}" onclick="selectScanType('${t.key}')">
      <span class="left"><i class="fa-solid ${t.icon}"></i>${t.label}</span>
      <span class="badge ${t.kind === 'passive' ? 'badge-green' : 'badge-yellow'}">${t.kind}</span>
    </div>`).join('');
}

function selectScanType(key) { selectedScanType = key; buildScanTypeList(); }

function populateScanPanel() {
  const sel = document.getElementById('scanAssetSelect');
  if (!sel) return;
  const prev = sel.value;
  sel.innerHTML = '<option value="">— Select asset —</option>' +
    allAssets.map(a => `<option value="${a.id}" ${a.id === prev ? 'selected' : ''}>${esc(a.name)} [${a.type}]</option>`).join('');
}

async function dispatchScan() {
  const id = document.getElementById('scanAssetSelect').value;
  if (!id) { alert('Select an asset first.'); return; }
  try {
    const r = await fetch(`${API}/assets/${id}/scan`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scan_type: selectedScanType }),
    });
    const d = await r.json();
    if (!r.ok) { alert(d.error); return; }
    await loadAllJobs(); refreshStats();
  } catch(e) { alert(e.message); }
}

// ── Job table ──────────────────────────────────────────────────────────────
function renderJobTable() {
  const tbody = document.getElementById('job-tbody');
  if (!allJobs.length) {
    tbody.innerHTML = `<tr><td colspan="5"><div class="empty"><i class="fa-solid fa-wave-square"></i>No scan jobs yet.</div></td></tr>`;
    return;
  }
  const iconMap = { pending:'fa-clock', running:'fa-spinner fa-spin', completed:'fa-circle-check', failed:'fa-circle-xmark', partial:'fa-triangle-exclamation' };
  const iconBg  = { pending:'job-icon-pending', running:'job-icon-running', completed:'job-icon-done', failed:'job-icon-failed', partial:'job-icon-running' };
  tbody.innerHTML = allJobs.slice(0, 40).map(j => {
    const st = j.status || 'pending';
    const started = j.started_at ? j.started_at.replace('T', ' ').substring(0, 16) : '—';
    return `<tr>
      <td><div class="job-icon ${iconBg[st]}"><i class="fa-solid ${iconMap[st]}"></i></div></td>
      <td style="font-weight:500">${esc(j._asset?.name || '—')}</td>
      <td><span class="badge badge-gray">${j.scan_type}</span></td>
      <td><span class="badge ${STATUS_BADGE[st] || 'badge-gray'}">${st}</span></td>
      <td style="color:var(--text-muted)">${started}</td>
    </tr>`;
  }).join('');
}

// ── Results ────────────────────────────────────────────────────────────────
document.getElementById('filterBar').addEventListener('click', e => {
  const chip = e.target.closest('.filter-chip');
  if (!chip) return;
  document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
  chip.classList.add('active');
  resultFilter = chip.dataset.filter;
  renderResults();
});

async function renderResults() {
  const container = document.getElementById('resultsContainer');
  const done = allJobs.filter(j =>
    j.status === 'completed' &&
    (resultFilter === 'all' || j.scan_type === resultFilter)
  );
  if (!done.length) {
    container.innerHTML = `<div class="empty"><i class="fa-solid fa-file-lines"></i>No results for this filter yet.</div>`;
    return;
  }
  const cards = await Promise.all(done.slice(0, 25).map(async j => {
    if (!j._results) {
      try {
        const r = await fetch(`${API}/scan-jobs/${j.id}/results`);
        const d = await r.json();
        j._results = d.results;
      } catch { j._results = []; }
    }
    return buildResultCard(j);
  }));
  container.innerHTML = cards.join('');
}

function buildResultCard(job) {
  const label = (SCAN_TYPES.find(t => t.key === job.scan_type) || { label: job.scan_type }).label;
  const date  = (job.ended_at || '').replace('T', ' ').substring(0, 16);
  const body  = formatResultBody(job.scan_type, job._results || []);
  return `<div class="result-block">
    <div class="result-header" onclick="this.nextElementSibling.style.display=this.nextElementSibling.style.display==='none'?'block':'none'">
      <div class="rh-left">
        <span class="badge badge-green"><i class="fa-solid fa-circle-check"></i></span>
        <span>${esc(job._asset?.name || '—')}</span>
        <span class="badge badge-gray">${label}</span>
      </div>
      <span class="rh-meta">${date} <i class="fa-solid fa-chevron-down" style="margin-left:4px;font-size:10px"></i></span>
    </div>
    <div class="result-body">${body}</div>
  </div>`;
}

function formatResultBody(type, results) {
  if (!results?.length) return `<span style="color:var(--text-subtle)">No data returned.</span>`;
  const r = results[0];
  if (!r) return `<span style="color:var(--text-subtle)">Empty result.</span>`;

  if (type === 'dns' && r.records) {
    const rows = Object.entries(r.records)
      .filter(([, v]) => v?.length)
      .map(([k, v]) => row(k, v.slice(0, 5).join(', ')));
    return rows.length ? rows.join('') : `<span style="color:var(--text-subtle)">No records found.</span>`;
  }
  if (type === 'whois') {
    return [
      r.registrar       && row('Registrar',    r.registrar),
      r.creation_date   && row('Created',      r.creation_date),
      r.expiry_date     && row('Expires',      r.expiry_date),
      r.status          && row('Status',       r.status),
    ].filter(Boolean).join('') || `<div class="code-block">${esc((r.raw||'').substring(0,400))}</div>`;
  }
  if (type === 'ssl' && r.certificate) {
    const c = r.certificate, d = c.days_until_expiry;
    const col = d < 30 ? 'var(--red-text)' : d < 90 ? 'var(--yellow-text)' : 'var(--green-text)';
    return [
      row('Subject',     c.subject),
      row('Issuer',      c.issuer),
      row('Valid until', c.valid_until),
      row('Days left',   `<span style="color:${col};font-weight:600">${d} days</span>`),
      row('TLS version', r.connection?.tls_version || '—'),
      row('Grade',       `<span class="badge badge-green">${r.grade || 'A'}</span>`),
      c.is_expired ? row('⚠', '<span style="color:var(--red-text)">Certificate expired</span>') : '',
    ].join('');
  }
  if (type === 'port') {
    const ports = r.open_ports || [];
    if (!ports.length) return `<span style="color:var(--green-text)"><i class="fa-solid fa-shield-halved"></i> No open ports detected</span>`;
    return ports.map(p =>
      row(`<span class="badge badge-red">:${p.port}</span>`,
          `<b>${p.service?.toUpperCase()}</b> / ${p.protocol}${p.version ? ' — ' + esc(p.version) : ''}`)
    ).join('') + `<div style="margin-top:6px;color:var(--text-subtle)">${r.total_scanned} ports scanned in ${r.scan_duration_ms}ms</div>`;
  }
  if (type === 'tech' && r.technologies) {
    return r.technologies.map(t =>
      row(`<span class="badge badge-gray">${esc(t.category)}</span>`,
          `<b>${esc(t.name)}</b>${t.version ? ' v' + esc(t.version) : ''} <span style="color:var(--text-subtle)">(${t.confidence}%)</span>`)
    ).join('');
  }
  if (type === 'ip' && r.geolocation) {
    const g = r.geolocation, a = r.asn || {};
    return [
      row('IP address', r.ip_address),
      row('Location',   [g.city, g.country].filter(Boolean).join(', ')),
      row('ISP',        g.isp || '—'),
      row('ASN',        `AS${a.number} — ${esc(a.description || '')}`),
      row('Reverse DNS', r.reverse_dns || '—'),
    ].join('');
  }
  if (type === 'subdomain' && r.subdomains) {
    if (!r.subdomains.length) return `<span style="color:var(--text-subtle)">No subdomains found.</span>`;
    return row('Found', `${r.subdomains.length} subdomains`) +
      r.subdomains.slice(0, 20).map(s => row('', esc(s))).join('');
  }
  if (type === 'cve') {
    const findings = r.cve_findings || [];
    if (!findings.length) return `<span style="color:var(--green-text)"><i class="fa-solid fa-shield-halved"></i> No CVEs found</span>`;
    return findings.flatMap(f => f.cves.map(c => {
      const bc = c.severity === 'CRITICAL' ? 'badge-red' : c.severity === 'HIGH' ? 'badge-yellow' : 'badge-gray';
      return row(`<span class="badge ${bc}">${c.severity}</span>`,
                 `<b>${esc(c.cve_id)}</b> (${esc(f.service)}:${f.port}) — ${esc(c.description)}`);
    })).join('');
  }
  return `<div class="code-block">${esc(JSON.stringify(r, null, 2).substring(0, 500))}</div>`;
}

function row(key, val) {
  return `<div class="result-row"><span class="result-key">${key}</span><span class="result-val">${val}</span></div>`;
}
function esc(s) {
  return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

window.addEventListener('DOMContentLoaded', init);