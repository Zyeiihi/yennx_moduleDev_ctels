const API_URL = "http://localhost:8080";

// Load Assets list into the dropdown select element
async function loadAssets() {
    const res = await fetch(`${API_URL}/assets`);
    const assets = await res.json();
    const select = document.getElementById("assetSelect");
    select.innerHTML = '<option value="">-- Select Asset --</option>';
    assets.forEach(asset => {
        select.innerHTML += `<option value="${asset.id}">${asset.name} (${asset.type.toUpperCase()})</option>`;
    });
}

// Add a new external asset to the monitoring system
async function addAsset() {
    const name = document.getElementById("assetName").value;
    const type = document.getElementById("assetType").value;
    if(!name) return alert("Please enter the asset name or target IP/Domain!");

    await fetch(`${API_URL}/assets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, type })
    });
    alert("Asset added successfully!");
    loadAssets();
}

// Trigger a asynchronous security scan job
async function triggerScan() {
    const assetId = document.getElementById("assetSelect").value;
    const scanType = document.getElementById("scanType").value;
    if(!assetId) return alert("Please select an asset to perform scanning!");

    const res = await fetch(`${API_URL}/assets/${assetId}/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scan_type: scanType })
    });
    const job = await res.json();
    alert(`Scan job scheduled successfully! Job ID: ${job.id}`);
    updateJobTable();
}

// Fetch scan jobs status from the API to update the dashboard table
async function updateJobTable() {
    const assetId = document.getElementById("assetSelect").value;
    if(!assetId) return;

    const res = await fetch(`${API_URL}/assets/${assetId}/scans`);
    const jobs = await res.json();
    const tbody = document.getElementById("jobTableBody");
    tbody.innerHTML = "";

    jobs.forEach(job => {
        const badgeClass = job.status === "completed" ? "bg-success" : "bg-warning";
        // Handle pending/running states nicely in English
        const resultsString = job.status === "completed" ? JSON.stringify(job.results) : "Processing...";
        tbody.innerHTML += `
            <tr>
                <td>${job.id.substring(0, 8)}...</td>
                <td><strong>${job.scan_type.toUpperCase()}</strong></td>
                <td><span class="badge ${badgeClass}">${job.status.toUpperCase()}</span></td>
                <td><code>${resultsString}</code></td>
            </tr>
        `;
    });
}

// Automatically poll and update the job table status every 3 seconds
setInterval(updateJobTable, 3000);
window.onload = loadAssets;