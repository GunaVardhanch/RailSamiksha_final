/**
 * RailSamiksha AI — Interactive Client-Side Engine for Vercel
 */

// Canonical Defect Data
const SAMPLE_DEFECTS = [
  {
    id: 1,
    name: "Rail Wear",
    severity: "LOW",
    conf: 0.88,
    box: [0.18, 0.42, 0.32, 0.65], // Normalized [x1, y1, x2, y2]
    chainage: "KM 122.400",
    lat: 28.6148,
    lon: 77.2096,
    action: "Schedule Rail Grinding within 90 days"
  },
  {
    id: 2,
    name: "Damaged Fastener",
    severity: "MEDIUM",
    conf: 0.79,
    box: [0.45, 0.52, 0.52, 0.61],
    chainage: "KM 122.415",
    lat: 28.6152,
    lon: 77.2099,
    action: "Replace Pandrol e-clip at Gang Inspection"
  },
  {
    id: 3,
    name: "Rail Crack",
    severity: "CRITICAL",
    conf: 0.91,
    box: [0.68, 0.38, 0.78, 0.49],
    chainage: "KM 122.430",
    lat: 28.6158,
    lon: 77.2104,
    action: "Immediate Emergency Speed Restriction (30 km/h) & Fishplate Clamp"
  }
];

let showBBoxes = true;
let currentConfThreshold = 0.30;
let mapInstance = null;

// Initialize when DOM loads
document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initStillCanvas();
  initVideoPlayer();
  initLedger();
});

// 1. Tab Navigation
function initTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      document.getElementById(targetId).classList.add("active");

      // Invalidate Leaflet Map Size if switching to map tab
      if (targetId === "map-tab") {
        setTimeout(initMap, 150);
      }
    });
  });
}

// 2. Still Image Canvas & Bounding Box Rendering
function initStillCanvas() {
  const img = document.getElementById("stillImage");
  const canvas = document.getElementById("overlayCanvas");
  const toggleBtn = document.getElementById("toggleBBoxBtn");
  const confSlider = document.getElementById("confSlider");
  const confVal = document.getElementById("confVal");

  function resizeCanvas() {
    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;
    drawBoundingBoxes();
  }

  if (img.complete) {
    resizeCanvas();
  } else {
    img.onload = resizeCanvas;
  }
  window.addEventListener("resize", resizeCanvas);

  confSlider.addEventListener("input", (e) => {
    currentConfThreshold = parseFloat(e.target.value) / 100.0;
    confVal.textContent = `${e.target.value}%`;
    drawBoundingBoxes();
    updateDefectsList();
  });

  toggleBtn.addEventListener("click", () => {
    showBBoxes = !showBBoxes;
    document.getElementById("bboxStatusText").textContent = showBBoxes ? "Visible" : "Hidden";
    drawBoundingBoxes();
  });

  document.getElementById("runStillInspectBtn").addEventListener("click", () => {
    drawBoundingBoxes();
    updateDefectsList();
  });

  updateDefectsList();
}

function drawBoundingBoxes() {
  const canvas = document.getElementById("overlayCanvas");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (!showBBoxes) return;

  const visibleDefects = SAMPLE_DEFECTS.filter(d => d.conf >= currentConfThreshold);

  visibleDefects.forEach(d => {
    const [nx1, ny1, nx2, ny2] = d.box;
    const x = nx1 * canvas.width;
    const y = ny1 * canvas.height;
    const w = (nx2 - nx1) * canvas.width;
    const h = (ny2 - ny1) * canvas.height;

    // Severity Colors
    let color = "#ef4444"; // Critical Red
    if (d.severity === "HIGH") color = "#f97316";
    if (d.severity === "MEDIUM") color = "#eab308";
    if (d.severity === "LOW") color = "#10b981";

    // Box stroke
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.strokeRect(x, y, w, h);

    // Pill Tag
    ctx.fillStyle = color;
    const label = `${d.name} ${(d.conf * 100).toFixed(0)}% [${d.severity}]`;
    ctx.font = "bold 11px Inter, sans-serif";
    const textW = ctx.measureText(label).width;

    ctx.fillRect(x, Math.max(0, y - 22), textW + 12, 22);

    ctx.fillStyle = "#ffffff";
    ctx.fillText(label, x + 6, Math.max(15, y - 7));
  });

  document.getElementById("stillDefectCount").textContent = visibleDefects.length;
}

function updateDefectsList() {
  const container = document.getElementById("defectsList");
  container.innerHTML = "";

  const visibleDefects = SAMPLE_DEFECTS.filter(d => d.conf >= currentConfThreshold);

  if (visibleDefects.length === 0) {
    container.innerHTML = `<div style="color: #64748b; font-size: 12px;">No defects meet current confidence threshold.</div>`;
    return;
  }

  visibleDefects.forEach(d => {
    let sevClass = "sev-low";
    if (d.severity === "CRITICAL") sevClass = "sev-critical";
    if (d.severity === "HIGH") sevClass = "sev-high";
    if (d.severity === "MEDIUM") sevClass = "sev-med";

    const item = document.createElement("div");
    item.style.cssText = "background: var(--bg-primary); padding: 8px 12px; border-radius: 6px; border: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; font-size: 12px;";
    item.innerHTML = `
      <div>
        <span style="font-weight: 600; color: #fff;">${d.name}</span>
        <span style="color: var(--text-muted); font-size: 11px; margin-left: 6px;">(${(d.conf * 100).toFixed(0)}%)</span>
      </div>
      <span class="sev-pill ${sevClass}">${d.severity}</span>
    `;
    container.appendChild(item);
  });
}

// 3. Video Player & Telemetry Synchronization
function initVideoPlayer() {
  const video = document.getElementById("patrolVideo");
  const timeDisplay = document.getElementById("videoTime");

  video.addEventListener("timeupdate", () => {
    const mins = Math.floor(video.currentTime / 60).toString().padStart(2, "0");
    const secs = (video.currentTime % 60).toFixed(1).padStart(4, "0");
    timeDisplay.textContent = `${mins}:${secs}s`;
  });
}

// 4. Georeferenced Leaflet Map
function initMap() {
  if (mapInstance) {
    mapInstance.invalidateSize();
    return;
  }

  const baseLat = 28.6148;
  const baseLon = 77.2096;

  mapInstance = L.map("mapContainer").setView([baseLat, baseLon], 16);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "© OpenStreetMap contributors"
  }).addTo(mapInstance);

  // Plot Defect Pins
  SAMPLE_DEFECTS.forEach(d => {
    let pinColor = "#ef4444";
    if (d.severity === "MEDIUM") pinColor = "#eab308";
    if (d.severity === "LOW") pinColor = "#10b981";

    const circle = L.circleMarker([d.lat, d.lon], {
      color: pinColor,
      fillColor: pinColor,
      fillOpacity: 0.8,
      radius: 8
    }).addTo(mapInstance);

    circle.bindPopup(`
      <div style="font-family: 'Inter', sans-serif; font-size: 12px;">
        <b style="font-size: 13px;">${d.name}</b><br>
        <b>Severity:</b> <span style="color: ${pinColor}; font-weight: 700;">${d.severity}</span><br>
        <b>Chainage:</b> ${d.chainage}<br>
        <b>Confidence:</b> ${(d.conf * 100).toFixed(0)}%<br>
        <b>GPS:</b> ${d.lat.toFixed(5)}°N, ${d.lon.toFixed(5)}°E
      </div>
    `);
  });
}

// 5. P-Way Maintenance Incident Registry
function initLedger() {
  const tbody = document.getElementById("ledgerTableBody");
  tbody.innerHTML = "";

  SAMPLE_DEFECTS.forEach(d => {
    let sevClass = "sev-low";
    if (d.severity === "CRITICAL") sevClass = "sev-critical";
    if (d.severity === "HIGH") sevClass = "sev-high";
    if (d.severity === "MEDIUM") sevClass = "sev-med";

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><span class="mono" style="color: var(--cyan-accent);">#TRK-00${d.id}</span></td>
      <td><b>${d.chainage}</b></td>
      <td>${d.name}</td>
      <td><span class="sev-pill ${sevClass}">${d.severity}</span></td>
      <td>${(d.conf * 100).toFixed(1)}%</td>
      <td class="mono">${d.lat.toFixed(6)}°N</td>
      <td class="mono">${d.lon.toFixed(6)}°E</td>
      <td style="color: var(--text-muted); font-size: 12px;">${d.action}</td>
    `;
    tbody.appendChild(tr);
  });

  // CSV Download
  document.getElementById("downloadCsvBtn").addEventListener("click", () => {
    const csvRows = [
      ["Track_ID", "Chainage_KM", "Defect_Category", "Severity", "Confidence_Pct", "Latitude", "Longitude", "Action_Required"],
      ...SAMPLE_DEFECTS.map(d => [
        `TRK-00${d.id}`,
        d.chainage,
        d.name,
        d.severity,
        (d.conf * 100).toFixed(1),
        d.lat,
        d.lon,
        `"${d.action}"`
      ])
    ];

    const csvContent = "data:text/csv;charset=utf-8," + csvRows.map(r => r.join(",")).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `RailSamiksha_PWay_Report_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  });
}
