const user = Auth.requireAuth(["Citizen"]);
if (user) document.getElementById("userName").textContent = `${user.full_name} (Citizen)`;

let allBins = [];

async function loadBins() {
  const zone = document.getElementById("zoneFilter").value;
  try {
    allBins = await apiRequest(zone ? `/bins?zone=${encodeURIComponent(zone)}` : "/bins");
    renderZoneOptions(allBins);
    renderBins(allBins);
    renderComplaintBinOptions(allBins);
  } catch (err) {
    showToast(err.message);
  }
}

function renderZoneOptions(bins) {
  const select = document.getElementById("zoneFilter");
  const current = select.value;
  const zones = [...new Set(bins.map((b) => b.zone))];
  select.innerHTML =
    `<option value="">All Zones</option>` +
    zones.map((z) => `<option value="${z}">${z}</option>`).join("");
  select.value = current;
}

function renderComplaintBinOptions(bins) {
  const select = document.getElementById("complaintBin");
  select.innerHTML =
    `<option value="">— General complaint —</option>` +
    bins.map((b) => `<option value="${b.id}">${b.bin_code} · ${b.location}</option>`).join("");
}

function renderBins(bins) {
  const grid = document.getElementById("binGrid");
  if (!bins.length) {
    grid.innerHTML = `<div class="empty-state">No bins found for this zone.</div>`;
    return;
  }
  grid.innerHTML = bins
    .map(
      (b) => `
    <div class="bin-card">
      <div class="bin-head">
        <span class="bin-code">${b.bin_code}</span>
        <span class="badge ${b.status}">${b.status}</span>
      </div>
      <div class="bin-meta">${b.location} · ${b.zone} · ${b.waste_type}</div>
      <div class="fill-bar-track">
        <div class="fill-bar ${fillBarClass(b.current_fill_level)}" style="width:${b.current_fill_level}%"></div>
      </div>
      <div class="bin-meta">${b.current_fill_level}% full · last collected ${formatDate(b.last_collected_at)}</div>
    </div>`
    )
    .join("");
}

document.getElementById("complaintForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const bin_id = document.getElementById("complaintBin").value || null;
  const reason = document.getElementById("complaintReason").value;
  try {
    await apiRequest("/complaints", { method: "POST", body: { bin_id, reason } });
    showToast("Complaint submitted");
    document.getElementById("complaintReason").value = "";
  } catch (err) {
    showToast(err.message);
  }
});

loadBins();
