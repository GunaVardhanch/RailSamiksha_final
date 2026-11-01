/**
 * RailSamiksha AI — Enterprise RBAC Platform Engine
 * Real-Time RT-DETR-L Aerial Defect Detection & P-Way TMS Analytics
 * Roles: Super Admin | Drone Operator | Defect Clearance Field Gang
 */

// ============================================================================
// 1. CENTRAL REACTIVE DATABASE STORE (TMS MASTER LEDGER)
// ============================================================================

const SURVEYS_DATABASE = [
  {
    id: "SURV-2026-001",
    corridor: "Agra Cantt Fast-Line (KM 88.200 - 90.100)",
    date: "2026-10-30",
    pilot: "Capt. R. Sharma (IR-8821)",
    clearanceGang: "Gang 08 (JE P-Way M. Kumar)",
    status: "CLEARED_100%",
    statusLabel: "✓ 100% Cleared",
    statusClass: "badge-green",
    coordinates: [
      [27.1767, 78.0081],
      [27.1780, 78.0105],
      [27.1802, 78.0140]
    ],
    defects: [
      {
        id: "DEF-001-A",
        name: "Damaged Fastener",
        category: "fastener",
        severity: "MEDIUM",
        chainage: "KM 88.350",
        lat: 27.1772,
        lon: 78.0090,
        action: "IRPWM Para 257: Replace Pandrol e-clip",
        cleared: true,
        clearedAt: "2026-10-30 14:22",
        repairedBy: "Gang 08"
      },
      {
        id: "DEF-001-B",
        name: "Rail Wear",
        category: "rail",
        severity: "LOW",
        chainage: "KM 89.120",
        lat: 27.1795,
        lon: 78.0125,
        action: "IRPWM Para 302: Rail profile grinding",
        cleared: true,
        clearedAt: "2026-10-30 16:45",
        repairedBy: "Gang 08"
      }
    ]
  },
  {
    id: "SURV-2026-002",
    corridor: "Rewari-Jaipur Chord (KM 45.000 - 47.200)",
    date: "2026-10-31",
    pilot: "Capt. S. Khan (IR-9104)",
    clearanceGang: "Gang 14 (JE P-Way S. Yadav)",
    status: "CLEARED_100%",
    statusLabel: "✓ 100% Cleared",
    statusClass: "badge-green",
    coordinates: [
      [28.1950, 76.6180],
      [28.1980, 76.6210],
      [28.2010, 76.6250]
    ],
    defects: [
      {
        id: "DEF-002-A",
        name: "Ballast Defect",
        category: "ballast",
        severity: "LOW",
        chainage: "KM 45.600",
        lat: 28.1965,
        lon: 76.6195,
        action: "IRPWM Para 223: Ballast packing & tamping",
        cleared: true,
        clearedAt: "2026-10-31 11:30",
        repairedBy: "Gang 14"
      }
    ]
  },
  {
    id: "SURV-2026-LIVE",
    corridor: "Delhi-Mathura Mainline (KM 122.400 - 122.800)",
    date: "2026-11-01 (Today)",
    pilot: "Capt. A. Verma (IR-9921)",
    clearanceGang: "Gang 12 (Sub-division Agra North)",
    status: "IN_SURVEY", // Will transition to SUBMITTED_FOR_CLEARANCE then to CLEARED_100%
    statusLabel: "● In Active Survey",
    statusClass: "badge-cyan",
    coordinates: [
      [28.6138, 77.2085],
      [28.6148, 77.2096],
      [28.6158, 77.2104],
      [28.6175, 77.2120]
    ],
    defects: [
      {
        id: "DEF-101",
        name: "Rail Wear (Gauge Flow)",
        category: "rail",
        severity: "LOW",
        conf: 0.88,
        box: [0.18, 0.42, 0.32, 0.65],
        chainage: "KM 122.400",
        lat: 28.6148,
        lon: 77.2096,
        action: "IRPWM Para 302: Schedule Rail Grinding within 90 days",
        cleared: false,
        verified: true
      },
      {
        id: "DEF-102",
        name: "Damaged Fastener (Clip Bend)",
        category: "fastener",
        severity: "MEDIUM",
        conf: 0.79,
        box: [0.45, 0.52, 0.52, 0.61],
        chainage: "KM 122.415",
        lat: 28.6152,
        lon: 77.2099,
        action: "IRPWM Para 257: Replace Pandrol e-clip at next gang inspection",
        cleared: false,
        verified: true
      },
      {
        id: "DEF-103",
        name: "Rail Crack (Transverse)",
        category: "rail",
        severity: "CRITICAL",
        conf: 0.91,
        box: [0.68, 0.38, 0.78, 0.49],
        chainage: "KM 122.430",
        lat: 28.6158,
        lon: 77.2104,
        action: "IRPWM Para 241: Emergency Speed Restriction (30 km/h) & Clamp Fishplates",
        cleared: false,
        verified: true
      }
    ]
  }
];

// Current Active State
let currentRole = "admin"; // 'admin' | 'operator' | 'clearance'
let currentScenarioKey = "scenario_fastener";
let currentConfThreshold = 0.30;
let activeCategoryFilter = "all";
let showBBoxes = true;
let selectedDefectId = null;

// Zoom and Pan
let zoomLevel = 1.0;
let panOffsetX = 0;
let panOffsetY = 0;
let isPanning = false;
let startPanX = 0;
let startPanY = 0;

// Leaflet Map Instances
let adminMap = null;
let clearanceMap = null;
let adminCorridorLayers = [];
let clearanceMarkers = [];

// ============================================================================
// 2. DOM INITIALIZATION
// ============================================================================

document.addEventListener("DOMContentLoaded", () => {
  initRoleSwitcher();
  initAdminDashboard();
  initOperatorWorkspace();
  initClearanceWorkspace();
  initModals();
  switchRole("admin");
});

// ============================================================================
// 3. ROLE-BASED ACCESS CONTROL (RBAC) SWITCHER
// ============================================================================

function initRoleSwitcher() {
  const roleBtns = document.querySelectorAll(".role-btn");
  roleBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetRole = btn.getAttribute("data-role");
      switchRole(targetRole);
    });
  });
}

function switchRole(role) {
  currentRole = role;

  // Update role buttons
  document.querySelectorAll(".role-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-role") === role);
  });

  // Update workspaces
  document.querySelectorAll(".role-workspace").forEach(ws => {
    ws.classList.remove("active");
  });
  const targetWs = document.getElementById(`${role}-workspace`);
  if (targetWs) targetWs.classList.add("active");

  // Update navbar role badge and footer
  const roleBadge = document.getElementById("roleBadge");
  const footerRole = document.getElementById("footerActiveRole");
  const bannerIcon = document.getElementById("roleBannerIcon");
  const bannerText = document.getElementById("roleBannerText");

  if (role === "admin") {
    roleBadge.textContent = "Super Admin Mode";
    roleBadge.className = "badge badge-cyan";
    footerRole.textContent = "Super Admin (HQ)";
    bannerIcon.textContent = "👑";
    bannerText.innerHTML = "<strong>Super Admin Executive Command:</strong> Full visibility into global flight surveys, live active patrols, central TMS CSV repository, and network-wide defect clearance metrics.";
    renderAdminView();
  } else if (role === "operator") {
    roleBadge.textContent = "Drone Operator Mode";
    roleBadge.className = "badge badge-purple";
    footerRole.textContent = "Field Drone Operator";
    bannerIcon.textContent = "🎮";
    bannerText.innerHTML = "<strong>Field Drone Operator Workspace:</strong> Review high-resolution 4K SAHI track orthophotos, verify AI defect bounding boxes, monitor live patrol flight feeds, and submit signed survey reports to the database.";
    renderOperatorView();
  } else if (role === "clearance") {
    roleBadge.textContent = "Defect Clearance Mode";
    roleBadge.className = "badge badge-green";
    footerRole.textContent = "P-Way Field Clearance Gang";
    bannerIcon.textContent = "🔧";
    bannerText.innerHTML = "<strong>P-Way Field Gang Remedial Portal:</strong> Locate georeferenced defects on track, execute required IRPWM remedial repairs (replacements/grinding/welds), and certify whole-section track safety clearance.";
    renderClearanceView();
  }
}

// ============================================================================
// 4. SUPER ADMIN PLATFORM LOGIC
// ============================================================================

function initAdminDashboard() {
  const exportBtn = document.getElementById("adminDownloadMasterCsvBtn");
  if (exportBtn) {
    exportBtn.addEventListener("click", exportMasterTMSCSV);
  }
}

function renderAdminView() {
  updateAdminKPIs();
  renderAdminSurveysTable();
  setTimeout(initOrUpdateAdminMap, 200);
}

function updateAdminKPIs() {
  const totalSurveys = SURVEYS_DATABASE.length;
  const liveSurveys = SURVEYS_DATABASE.filter(s => s.status === "IN_SURVEY").length;

  let totalDefects = 0;
  let clearedDefects = 0;

  SURVEYS_DATABASE.forEach(s => {
    s.defects.forEach(d => {
      totalDefects++;
      if (d.cleared) clearedDefects++;
    });
  });

  const pendingDefects = totalDefects - clearedDefects;
  const clearanceRate = totalDefects > 0 ? ((clearedDefects / totalDefects) * 100).toFixed(1) : 0;

  document.getElementById("adminTotalSurveys").textContent = `${totalSurveys} Surveys`;
  document.getElementById("adminLiveSurveys").innerHTML = liveSurveys > 0 ? 
    `<span class="pulse-dot" style="display: inline-block; vertical-align: middle; margin-right: 4px;"></span> ${liveSurveys} Flight` : "0 Flights";
  document.getElementById("adminTotalDefects").textContent = `${totalDefects} Defects`;
  document.getElementById("adminClearanceRatio").textContent = `${clearedDefects} / ${pendingDefects}`;
  document.getElementById("adminClearancePct").textContent = `${clearanceRate}% Divisional Clearance Rate`;

  // Update Clearance counter badge
  const pendingSurveyCount = SURVEYS_DATABASE.filter(s => s.status === "SUBMITTED_FOR_CLEARANCE").length;
  const alertBadge = document.getElementById("clearanceAlertBadge");
  if (alertBadge) {
    alertBadge.textContent = pendingSurveyCount;
    alertBadge.style.display = pendingSurveyCount > 0 ? "inline-block" : "none";
  }
}

function renderAdminSurveysTable() {
  const tbody = document.getElementById("adminSurveysTableBody");
  if (!tbody) return;

  tbody.innerHTML = "";

  SURVEYS_DATABASE.forEach(s => {
    const tr = document.createElement("tr");

    let statusPill = `<span class="badge ${s.statusClass}">${s.statusLabel}</span>`;
    if (s.status === "IN_SURVEY") {
      statusPill = `<span class="badge badge-cyan"><span class="pulse-dot"></span> In Survey</span>`;
    } else if (s.status === "SUBMITTED_FOR_CLEARANCE") {
      statusPill = `<span class="badge" style="background: rgba(234, 179, 8, 0.2); color: #fbbf24; border: 1px solid #fbbf24;">Pending Clearance</span>`;
    }

    const defectCount = s.defects.length;
    const clearedCount = s.defects.filter(d => d.cleared).length;

    tr.innerHTML = `
      <td><strong>${s.id}</strong></td>
      <td>${s.corridor}</td>
      <td>${s.date}</td>
      <td><span style="font-weight: 600;">${defectCount}</span> (${clearedCount} cleared)</td>
      <td>${statusPill}</td>
      <td>
        <button class="btn-secondary" onclick="exportSingleSurveyCSV('${s.id}')" style="padding: 4px 8px; font-size: 11px;">
          📥 CSV
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function initOrUpdateAdminMap() {
  const container = document.getElementById("adminMapContainer");
  if (!container) return;

  if (!adminMap) {
    adminMap = L.map('adminMapContainer').setView([28.6148, 77.2096], 14);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
      maxZoom: 19
    }).addTo(adminMap);
  } else {
    adminMap.invalidateSize();
  }

  // Clear layers
  adminCorridorLayers.forEach(l => adminMap.removeLayer(l));
  adminCorridorLayers = [];

  // Plot Corridors
  SURVEYS_DATABASE.forEach(s => {
    let color = "#10b981"; // Cleared Green
    if (s.status === "IN_SURVEY") color = "#06b6d4"; // Active Cyan
    if (s.status === "SUBMITTED_FOR_CLEARANCE") color = "#fbbf24"; // Amber

    const poly = L.polyline(s.coordinates, {
      color: color,
      weight: s.status === "IN_SURVEY" ? 5 : 4,
      dashArray: s.status === "IN_SURVEY" ? "6, 6" : null
    }).addTo(adminMap);

    poly.bindPopup(`
      <div style="font-family: 'Inter', sans-serif; font-size: 12px; color: #0f172a;">
        <strong>${s.id}</strong><br>
        <span>${s.corridor}</span><br>
        <strong>Status:</strong> ${s.statusLabel}<br>
        <strong>Defects:</strong> ${s.defects.length}
      </div>
    `);

    adminCorridorLayers.push(poly);

    // If live drone survey, plot drone icon
    if (s.status === "IN_SURVEY") {
      const droneHead = s.coordinates[s.coordinates.length - 1];
      const droneMarker = L.circleMarker(droneHead, {
        radius: 10,
        fillColor: "#06b6d4",
        color: "#ffffff",
        weight: 3,
        fillOpacity: 0.9
      }).addTo(adminMap);
      droneMarker.bindPopup("<strong>DRONE FLIGHT 104</strong><br>Capturing 4K SAHI video stream.");
      adminCorridorLayers.push(droneMarker);
    }
  });

  // Fit bounds to live survey
  const liveSurvey = SURVEYS_DATABASE.find(s => s.id === "SURV-2026-LIVE");
  if (liveSurvey) {
    adminMap.setView(liveSurvey.coordinates[1], 15);
  }
}

// ============================================================================
// 5. OPERATOR WORKSPACE LOGIC
// ============================================================================

function initOperatorWorkspace() {
  const opTabBtns = document.querySelectorAll(".op-tab-btn");
  opTabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      opTabBtns.forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".op-tab-content").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      const targetId = btn.getAttribute("data-optab");
      document.getElementById(targetId).classList.add("active");
    });
  });

  initStillCanvas();
  initVideoPlayer();

  const submitSurveyBtn = document.getElementById("operatorSubmitSurveyBtn");
  if (submitSurveyBtn) {
    submitSurveyBtn.addEventListener("click", openSubmitModal);
  }
}

function renderOperatorView() {
  drawBoundingBoxes();
  renderOperatorDefectsList();
}

function initStillCanvas() {
  const img = document.getElementById("stillImage");
  const canvas = document.getElementById("overlayCanvas");
  const wrapper = document.getElementById("canvasWrapper");

  function resizeCanvas() {
    canvas.width = wrapper.clientWidth;
    canvas.height = wrapper.clientHeight;
    drawBoundingBoxes();
  }

  if (img.complete) resizeCanvas();
  else img.onload = resizeCanvas;
  window.addEventListener("resize", resizeCanvas);

  // Zoom and Pan
  wrapper.addEventListener("wheel", (e) => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.15 : 0.87;
    zoomLevel = Math.min(Math.max(zoomLevel * factor, 1.0), 5.0);
    if (zoomLevel === 1.0) { panOffsetX = 0; panOffsetY = 0; }
    applyCanvasTransform();
  });

  wrapper.addEventListener("mousedown", (e) => {
    if (zoomLevel > 1.0) {
      isPanning = true;
      startPanX = e.clientX - panOffsetX;
      startPanY = e.clientY - panOffsetY;
    }
  });

  window.addEventListener("mousemove", (e) => {
    if (!isPanning) return;
    panOffsetX = e.clientX - startPanX;
    panOffsetY = e.clientY - startPanY;
    applyCanvasTransform();
  });

  window.addEventListener("mouseup", () => { isPanning = false; });

  document.getElementById("zoomInBtn").addEventListener("click", () => {
    zoomLevel = Math.min(zoomLevel * 1.25, 5.0);
    applyCanvasTransform();
  });
  document.getElementById("zoomOutBtn").addEventListener("click", () => {
    zoomLevel = Math.max(zoomLevel / 1.25, 1.0);
    if (zoomLevel === 1.0) { panOffsetX = 0; panOffsetY = 0; }
    applyCanvasTransform();
  });
  document.getElementById("resetZoomBtn").addEventListener("click", () => {
    zoomLevel = 1.0; panOffsetX = 0; panOffsetY = 0;
    applyCanvasTransform();
  });

  // Controls
  const confSlider = document.getElementById("confSlider");
  const confVal = document.getElementById("confVal");
  confSlider.addEventListener("input", (e) => {
    currentConfThreshold = parseFloat(e.target.value) / 100.0;
    confVal.textContent = `${e.target.value}%`;
    drawBoundingBoxes();
  });

  document.getElementById("toggleBBoxBtn").addEventListener("click", () => {
    showBBoxes = !showBBoxes;
    document.getElementById("bboxStatusText").textContent = showBBoxes ? "Visible" : "Hidden";
    drawBoundingBoxes();
  });

  document.getElementById("scenarioSelect").addEventListener("change", (e) => {
    currentScenarioKey = e.target.value;
    const imgEl = document.getElementById("stillImage");
    if (currentScenarioKey === "scenario_fracture") {
      imgEl.src = "sample_data/track_fracture_sample.jpg";
    } else {
      imgEl.src = "sample_data/sample_track_image.jpg";
    }
    imgEl.onload = () => drawBoundingBoxes();
  });
}

function applyCanvasTransform() {
  const img = document.getElementById("stillImage");
  img.style.transform = `translate(${panOffsetX}px, ${panOffsetY}px) scale(${zoomLevel})`;
  drawBoundingBoxes();
}

function drawBoundingBoxes() {
  const canvas = document.getElementById("overlayCanvas");
  const img = document.getElementById("stillImage");
  if (!canvas || !img) return;

  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!showBBoxes) return;

  const liveSurvey = SURVEYS_DATABASE.find(s => s.id === "SURV-2026-LIVE");
  if (!liveSurvey) return;

  const imgRect = img.getBoundingClientRect();
  const wrapperRect = canvas.parentElement.getBoundingClientRect();
  const imgLeft = imgRect.left - wrapperRect.left;
  const imgTop = imgRect.top - wrapperRect.top;
  const imgW = imgRect.width;
  const imgH = imgRect.height;

  liveSurvey.defects.forEach(d => {
    if (!d.verified) return;
    const [nx1, ny1, nx2, ny2] = d.box;
    const x = imgLeft + nx1 * imgW;
    const y = imgTop + ny1 * imgH;
    const w = (nx2 - nx1) * imgW;
    const h = (ny2 - ny1) * imgH;

    let color = "#ef4444";
    if (d.severity === "MEDIUM") color = "#eab308";
    if (d.severity === "LOW") color = "#10b981";

    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.5;
    ctx.strokeRect(x, y, w, h);

    ctx.fillStyle = "rgba(7, 11, 18, 0.85)";
    const label = `${d.name} ${(d.conf * 100).toFixed(0)}% [${d.severity}]`;
    ctx.font = "bold 11px Inter, sans-serif";
    const textW = ctx.measureText(label).width;
    ctx.fillRect(x, Math.max(0, y - 22), textW + 10, 20);

    ctx.fillStyle = color;
    ctx.fillText(label, x + 5, Math.max(14, y - 7));
    ctx.restore();
  });
}

function renderOperatorDefectsList() {
  const listEl = document.getElementById("operatorDefectsList");
  const tallyEl = document.getElementById("operatorVerifiedTally");
  if (!listEl) return;

  listEl.innerHTML = "";

  const liveSurvey = SURVEYS_DATABASE.find(s => s.id === "SURV-2026-LIVE");
  if (!liveSurvey) return;

  const verifiedCount = liveSurvey.defects.filter(d => d.verified).length;
  tallyEl.textContent = `${verifiedCount} Verified`;

  liveSurvey.defects.forEach(d => {
    const card = document.createElement("div");
    card.className = "punch-card";

    let sevClass = d.severity === "CRITICAL" ? "sev-high" : (d.severity === "MEDIUM" ? "sev-med" : "sev-low");

    card.innerHTML = `
      <div class="punch-card-header">
        <div>
          <strong style="color: #fff; font-size: 13px;">${d.id} • ${d.name}</strong>
          <div style="font-size: 11px; color: var(--text-muted);">${d.chainage} • ${(d.conf * 100).toFixed(0)}% Conf</div>
        </div>
        <span class="sev-pill ${sevClass}">${d.severity}</span>
      </div>
      <div style="font-size: 11px; color: #94a3b8;">${d.action}</div>
      <div class="punch-action-bar">
        <span style="font-size: 11px; color: ${d.verified ? '#34d399' : '#f87171'};">
          ${d.verified ? '✓ Verified by Pilot' : '✗ Marked False Alarm'}
        </span>
        <button class="btn-secondary" onclick="toggleOperatorVerification('${d.id}')" style="padding: 4px 8px; font-size: 11px;">
          ${d.verified ? 'Reject' : 'Verify'}
        </button>
      </div>
    `;
    listEl.appendChild(card);
  });
}

window.toggleOperatorVerification = function(defectId) {
  const liveSurvey = SURVEYS_DATABASE.find(s => s.id === "SURV-2026-LIVE");
  if (!liveSurvey) return;
  const defect = liveSurvey.defects.find(d => d.id === defectId);
  if (defect) {
    defect.verified = !defect.verified;
    drawBoundingBoxes();
    renderOperatorDefectsList();
  }
};

function initVideoPlayer() {
  const video = document.getElementById("patrolVideo");
  const videoSelect = document.getElementById("videoSelect");
  if (!video || !videoSelect) return;

  videoSelect.addEventListener("change", (e) => {
    video.src = e.target.value;
    video.play();
  });

  video.addEventListener("timeupdate", () => {
    const cur = video.currentTime;
    const mins = Math.floor(cur / 60);
    const secs = (cur % 60).toFixed(1);
    document.getElementById("videoTime").textContent = `${mins.toString().padStart(2, '0')}:${secs.padStart(4, '0')}s`;

    document.getElementById("vSpd").textContent = `${(6.4 + Math.sin(cur * 0.8) * 0.6).toFixed(1)} km/h`;
    document.getElementById("vAlt").textContent = `${(3.8 + Math.cos(cur * 0.5) * 0.2).toFixed(2)} m`;
    document.getElementById("vLat").textContent = `${(28.614800 + cur * 0.00008).toFixed(4)}° N`;
    document.getElementById("vKm").textContent = `KM ${(122.400 + cur * 0.002).toFixed(3)}`;
  });
}

// ============================================================================
// 6. DEFECT CLEARANCE PLATFORM LOGIC (P-WAY FIELD GANG)
// ============================================================================

function initClearanceWorkspace() {
  const certifyBtn = document.getElementById("certifySectionClearanceBtn");
  if (certifyBtn) {
    certifyBtn.addEventListener("click", certifySectionClearance);
  }
}

function renderClearanceView() {
  renderClearancePunchlist();
  setTimeout(initOrUpdateClearanceMap, 200);
}

function renderClearancePunchlist() {
  const punchlistEl = document.getElementById("clearancePunchlist");
  const progressText = document.getElementById("clearanceProgressText");
  const certifyBtn = document.getElementById("certifySectionClearanceBtn");
  const statusTag = document.getElementById("clearanceStatusTag");
  if (!punchlistEl) return;

  punchlistEl.innerHTML = "";

  const liveSurvey = SURVEYS_DATABASE.find(s => s.id === "SURV-2026-LIVE");
  if (!liveSurvey) return;

  const totalDefects = liveSurvey.defects.length;
  const clearedCount = liveSurvey.defects.filter(d => d.cleared).length;

  progressText.textContent = `${clearedCount} / ${totalDefects} Repaired`;

  if (liveSurvey.status === "CLEARED_100%") {
    statusTag.textContent = "✓ 100% CLEARED & CERTIFIED";
    statusTag.style.color = "#34d399";
    certifyBtn.disabled = true;
    certifyBtn.textContent = "✓ Section Track Safety Certified";
  } else if (liveSurvey.status === "SUBMITTED_FOR_CLEARANCE") {
    statusTag.textContent = "ACTION REQUIRED (DISPATCHED)";
    statusTag.style.color = "#fbbf24";
    certifyBtn.disabled = (clearedCount < totalDefects);
  } else {
    statusTag.textContent = "DRONE SURVEY IN PROGRESS";
    statusTag.style.color = "#38bdf8";
    certifyBtn.disabled = true;
  }

  liveSurvey.defects.forEach(d => {
    const card = document.createElement("div");
    card.className = `punch-card ${d.cleared ? 'cleared' : ''}`;

    let sevClass = d.severity === "CRITICAL" ? "sev-high" : (d.severity === "MEDIUM" ? "sev-med" : "sev-low");

    card.innerHTML = `
      <div class="punch-card-header">
        <div>
          <strong style="color: #fff; font-size: 13px;">${d.id} • ${d.name}</strong>
          <div style="font-size: 11px; color: var(--text-muted);">${d.chainage} • Lat ${d.lat.toFixed(4)}°, Lon ${d.lon.toFixed(4)}°</div>
        </div>
        <span class="sev-pill ${sevClass}">${d.severity}</span>
      </div>
      <div style="font-size: 12px; color: #fbbf24; background: rgba(15, 23, 42, 0.7); padding: 8px; border-radius: 4px; border: 1px solid var(--border-color);">
        <strong>Required Standard:</strong> ${d.action}
      </div>
      <div class="punch-action-bar">
        <span style="font-size: 11px; color: ${d.cleared ? '#34d399' : '#fbbf24'}; font-weight: 600;">
          ${d.cleared ? `✓ Repaired by Gang 12 (${d.clearedAt || 'Just Now'})` : '● Pending Ground Repair'}
        </span>
        <button class="punch-toggle-btn ${d.cleared ? 'cleared' : ''}" onclick="toggleDefectCleared('${d.id}')">
          ${d.cleared ? '✓ Cleared' : 'Mark Cleared'}
        </button>
      </div>
    `;

    card.addEventListener("click", () => showClearanceDetail(d));
    punchlistEl.appendChild(card);
  });
}

function showClearanceDetail(d) {
  document.getElementById("clDetailChainage").textContent = d.chainage;
  document.getElementById("clDetailCoords").textContent = `${d.lat.toFixed(6)}° N, ${d.lon.toFixed(6)}° E`;
  document.getElementById("clDetailAction").textContent = d.action;
  const sevEl = document.getElementById("clDetailSeverity");
  sevEl.textContent = d.severity;
  sevEl.className = `sev-pill ${d.severity === 'CRITICAL' ? 'sev-high' : (d.severity === 'MEDIUM' ? 'sev-med' : 'sev-low')}`;

  if (clearanceMap) {
    clearanceMap.setView([d.lat, d.lon], 18);
  }
}

window.toggleDefectCleared = function(defectId) {
  const liveSurvey = SURVEYS_DATABASE.find(s => s.id === "SURV-2026-LIVE");
  if (!liveSurvey) return;

  const defect = liveSurvey.defects.find(d => d.id === defectId);
  if (defect) {
    defect.cleared = !defect.cleared;
    if (defect.cleared) {
      const now = new Date();
      defect.clearedAt = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    }
    renderClearancePunchlist();
    updateAdminKPIs();
  }
};

function certifySectionClearance() {
  const liveSurvey = SURVEYS_DATABASE.find(s => s.id === "SURV-2026-LIVE");
  if (!liveSurvey) return;

  liveSurvey.status = "CLEARED_100%";
  liveSurvey.statusLabel = "✓ 100% Cleared";
  liveSurvey.statusClass = "badge-green";

  alert("🛡️ TRACK SAFETY CERTIFIED!\n\nAll defects in Section Delhi-Mathura (KM 122.4 - 122.8) have been verified repaired by Gang 12.\nSuper Admin dashboard has been notified and updated.");

  renderClearanceView();
  updateAdminKPIs();
}

function initOrUpdateClearanceMap() {
  const container = document.getElementById("clearanceMapContainer");
  if (!container) return;

  const liveSurvey = SURVEYS_DATABASE.find(s => s.id === "SURV-2026-LIVE");
  if (!liveSurvey) return;

  if (!clearanceMap) {
    clearanceMap = L.map('clearanceMapContainer').setView([28.6148, 77.2096], 17);

    // Esri World Imagery (Satellite HD)
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Esri Satellite',
      maxZoom: 19
    }).addTo(clearanceMap);
  } else {
    clearanceMap.invalidateSize();
  }

  clearanceMarkers.forEach(m => clearanceMap.removeLayer(m));
  clearanceMarkers = [];

  liveSurvey.defects.forEach(d => {
    let pinColor = d.cleared ? '#10b981' : (d.severity === 'CRITICAL' ? '#ef4444' : '#eab308');

    const m = L.circleMarker([d.lat, d.lon], {
      radius: 9,
      fillColor: pinColor,
      color: '#ffffff',
      weight: 2,
      fillOpacity: 0.9
    }).addTo(clearanceMap);

    m.bindPopup(`<strong>${d.id} • ${d.name}</strong><br>Chainage: ${d.chainage}<br>Status: ${d.cleared ? 'Cleared' : 'Pending'}`);
    clearanceMarkers.push(m);
  });
}

// ============================================================================
// 7. OPERATOR SURVEY SUBMISSION MODAL
// ============================================================================

function initModals() {
  const modal = document.getElementById("submitModal");
  const closeBtn = document.getElementById("closeModalBtn");
  const cancelBtn = document.getElementById("cancelModalBtn");
  const confirmBtn = document.getElementById("confirmSubmitSurveyBtn");

  if (closeBtn) closeBtn.addEventListener("click", () => modal.style.display = "none");
  if (cancelBtn) cancelBtn.addEventListener("click", () => modal.style.display = "none");
  if (confirmBtn) confirmBtn.addEventListener("click", submitSurveyToTMS);
}

function openSubmitModal() {
  const liveSurvey = SURVEYS_DATABASE.find(s => s.id === "SURV-2026-LIVE");
  if (!liveSurvey) return;

  const verifiedCount = liveSurvey.defects.filter(d => d.verified).length;
  document.getElementById("modalDefectsCount").textContent = `${verifiedCount} Verified Defects`;
  document.getElementById("modalTimestamp").textContent = new Date().toLocaleString();
  document.getElementById("submitModal").style.display = "flex";
}

function submitSurveyToTMS() {
  const liveSurvey = SURVEYS_DATABASE.find(s => s.id === "SURV-2026-LIVE");
  if (!liveSurvey) return;

  liveSurvey.status = "SUBMITTED_FOR_CLEARANCE";
  liveSurvey.statusLabel = "Pending Clearance";
  liveSurvey.statusClass = "badge-purple";

  document.getElementById("submitModal").style.display = "none";

  alert("✅ SURVEY SUBMITTED TO TMS DATABASE!\n\nOfficial CSV dispatch generated and committed.\nField Gang 12 has been notified to execute defect clearance.");

  // Switch to Clearance view so user can experience the flow!
  switchRole("clearance");
}

// ============================================================================
// 8. MASTER CSV EXPORT (INDIAN RAILWAYS TMS FORMAT)
// ============================================================================

window.exportSingleSurveyCSV = function(surveyId) {
  const survey = SURVEYS_DATABASE.find(s => s.id === surveyId);
  if (!survey) return;

  let csv = "Survey_ID,Corridor,Date,Defect_ID,Defect_Category,Severity,Chainage,Latitude,Longitude,IRPWM_Remedial_Standard,Clearance_Status\n";
  survey.defects.forEach(d => {
    csv += `"${survey.id}","${survey.corridor}","${survey.date}","${d.id}","${d.name}","${d.severity}","${d.chainage}",${d.lat},${d.lon},"${d.action}","${d.cleared ? 'CLEARED' : 'PENDING'}"\n`;
  });

  downloadCSVFile(csv, `RailSamiksha_TMS_${survey.id}.csv`);
};

function exportMasterTMSCSV() {
  let csv = "Survey_ID,Corridor,Date,Pilot,Clearance_Gang,Survey_Status,Defect_ID,Defect_Category,Severity,Chainage,Latitude,Longitude,Clearance_Status\n";

  SURVEYS_DATABASE.forEach(s => {
    s.defects.forEach(d => {
      csv += `"${s.id}","${s.corridor}","${s.date}","${s.pilot}","${s.clearanceGang}","${s.status}","${d.id}","${d.name}","${d.severity}","${d.chainage}",${d.lat},${d.lon},"${d.cleared ? 'CLEARED' : 'PENDING'}"\n`;
    });
  });

  downloadCSVFile(csv, `RailSamiksha_Master_TMS_Ledger_${new Date().toISOString().split('T')[0]}.csv`);
}

function downloadCSVFile(csvContent, fileName) {
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", fileName);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
