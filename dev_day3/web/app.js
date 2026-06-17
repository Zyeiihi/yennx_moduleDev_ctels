const API_URL = "http://localhost:8080";

// Tải danh sách Asset đổ vào Dropdown select
async function loadAssets() {
    const res = await fetch(`${API_URL}/assets`);
    const assets = await res.json();
    const select = document.getElementById("assetSelect");
    select.innerHTML = '<option value="">-- Chọn Asset --</option>';
    assets.forEach(asset => {
        select.innerHTML += `<option value="${asset.id}">${asset.name} (${asset.type})</option>`;
    });
}

async function addAsset() {
    const name = document.getElementById("assetName").value;
    const type = document.getElementById("assetType").value;
    if(!name) return alert("Vui lòng nhập tên tài sản!");

    await fetch(`${API_URL}/assets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, type })
    });
    alert("Thêm tài sản thành công!");
    loadAssets();
}

async function triggerScan() {
    const assetId = document.getElementById("assetSelect").value;
    const scanType = document.getElementById("scanType").value;
    if(!assetId) return alert("Vui lòng chọn một tài sản!");

    const res = await fetch(`${API_URL}/assets/${assetId}/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scan_type: scanType })
    });
    const job = await res.json();
    alert(`Đã lập lịch thành công Job ID: ${job.id}`);
    updateJobTable();
}

async function updateJobTable() {
    // Đọc trạng thái các Job từ API để hiển thị lên bảng điều khiển công cụ
    const assetId = document.getElementById("assetSelect").value;
    if(!assetId) return;

    const res = await fetch(`${API_URL}/assets/${assetId}/scans`);
    const jobs = await res.json();
    const tbody = document.getElementById("jobTableBody");
    tbody.innerHTML = "";

    jobs.forEach(job => {
        const badgeClass = job.status === "completed" ? "bg-success" : "bg-warning";
        const resultsString = JSON.stringify(job.results) || "Đang xử lý...";
        tbody.innerHTML += `
            <tr>
                <td>${job.id.substring(0, 8)}...</td>
                <td><strong>${job.scan_type.toUpperCase()}</strong></td>
                <td><span class="badge ${badgeClass}">${job.status}</span></td>
                <td><code>${resultsString}</code></td>
            </tr>
        `;
    });
}

// Tự động reload cập nhật trạng thái sau mỗi 3 giây
setInterval(updateJobTable, 3000);
window.onload = loadAssets;