const API_URL = "http://localhost:8080";

// Biến cục bộ để đếm tổng số Job và Lỗ hổng phục vụ Widget
let totalAssets = 0;
let totalJobs = 0;
let discoveredRisks = 0;

async function loadAssets() {
    const res = await fetch(`${API_URL}/assets`);
    const assets = await res.json();
    totalAssets = assets.length;
    document.getElementById("widgetAssetsCount").innerText = totalAssets;

    const select = document.getElementById("assetSelect");
    select.innerHTML = '<option value="">-- Select Scope --</option>';
    assets.forEach(asset => {
        select.innerHTML += `<option value="${asset.id}">${asset.name} [${asset.type.toUpperCase()}]</option>`;
    });
}

async function addAsset() {
    const name = document.getElementById("assetName").value;
    const type = document.getElementById("assetType").value;
    if(!name) return alert("Validation Error: Destination target entry cannot be empty!");

    await fetch(`${API_URL}/assets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, type })
    });
    alert("Asset successfully linked to monitoring console.");
    document.getElementById("assetName").value = "";
    loadAssets();
}

async function triggerScan() {
    const assetId = document.getElementById("assetSelect").value;
    const scanType = document.getElementById("scanType").value;
    if(!assetId) return alert("Operational Error: Select a scoped target before execution!");

    const res = await fetch(`${API_URL}/assets/${assetId}/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scan_type: scanType })
    });
    const job = await res.json();
    alert(`Security task dispatched! Tracking ID: ${job.id}`);
    updateJobTable();
}

// Hàm format dữ liệu thô từ API sang giao diện cấu trúc SOC trực quan
function formatIntelligenceOutput(job) {
    if (job.status !== "completed") {
        return `<span style="color: var(--accent-warning); font-style: italic;"><i class="fa-solid fa-spinner fa-spin"></i> Awaiting pipeline results processing...</span>`;
    }

    const data = job.results;
    if (!data || data.error) return `<span class="severity sev-critical">Scan Fault: ${data?.error || 'Unknown Pipeline Failure'}</span>`;

    let html = "";
    
    // 1. Nếu là quét Port
    if (job.scan_type === "port" && data.open_ports) {
        if (data.open_ports.length === 0) {
            html += `<span class="severity sev-safe"><i class="fa-solid fa-check-double"></i> Hardened: No Common Port Overlaps Found</span>`;
        } else {
            data.open_ports.forEach(p => {
                // Đếm nguy cơ bảo mật nếu mở cổng nhạy cảm như 22, 8080, 5432
                discoveredRisks++;
                html += `<div style="margin-bottom: 4px;">
                    <span class="severity sev-critical">OPEN PORT ${p.port}</span> 
                    <strong style="color: var(--accent-blue)">[${p.service.toUpperCase()}]</strong> - <em>${p.version}</em>
                </div>`;
            });
        }
        return html;
    }

    // 2. Nếu là quét TLS/SSL Cert
    if (job.scan_type === "ssl" && data.certificate) {
        html += `<div><strong>Issuer:</strong> ${data.certificate.issuer}</div>`;
        html += `<div><strong>Valid Until:</strong> <span style="color: var(--accent-green)">${data.certificate.valid_until}</span></div>`;
        html += `<div><strong>Cipher:</strong> <code style="color: var(--accent-blue)">${data.connection.cipher_suite}</code> (${data.connection.tls_version})</div>`;
        return html;
    }

    // 3. Nếu là nhận diện công nghệ Tech Fingerprint
    if (job.scan_type === "tech" && data.technologies) {
        data.technologies.forEach(t => {
            html += `<span class="severity sev-medium"><i class="fa-solid fa-microchip"></i> ${t.name} (${t.category})</span> `;
        });
        return html;
    }

    // Fallback mặc định cho các loại scan khác (GeoIP...)
    return `<div class="result-block">${JSON.stringify(data, null, 2)}</div>`;
}

async function updateJobTable() {
    const assetId = document.getElementById("assetSelect").value;
    if(!assetId) return;

    const res = await fetch(`${API_URL}/assets/${assetId}/scans`);
    const jobs = await res.json();
    
    // Cập nhật số lượng Job cho Widget
    totalJobs = jobs.length;
    document.getElementById("widgetJobsCount").innerText = totalJobs;
    
    const tbody = document.getElementById("jobTableBody");
    tbody.innerHTML = "";

    // Reset bộ đếm rủi ro tạm thời trước khi lặp qua bảng dữ liệu
    discoveredRisks = 0;

    if(jobs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No scan historical records found for this scope.</td></tr>`;
        document.getElementById("widgetRisksCount").innerText = 0;
        return;
    }

    jobs.forEach(job => {
        const badgeClass = job.status === "completed" ? "bg-completed" : "bg-processing";
        const statusLabel = job.status === "completed" ? "COMPLETED" : "RUNNING";
        const formattedOutput = formatIntelligenceOutput(job);

        tbody.innerHTML += `
            <tr>
                <td><i class="fa-solid fa-fingerprint" style="color: var(--text-muted)"></i> <code>${job.id.substring(0, 8)}</code></td>
                <td><strong>${job.scan_type.toUpperCase()}</strong></td>
                <td><span class="badge ${badgeClass}">${statusLabel}</span></td>
                <td>${formattedOutput}</td>
            </tr>
        `;
    });

    // Cập nhật số rủi ro đếm được lên widget sau khi render xong
    document.getElementById("widgetRisksCount").innerText = discoveredRisks;
}

// Polling định kỳ cập nhật bảng dữ liệu sau mỗi 3 giây
setInterval(updateJobTable, 3000);
window.onload = loadAssets;