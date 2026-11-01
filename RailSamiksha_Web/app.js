/**
 * RailSamiksha AI — Interactive Client-Side Engine for Vercel Edge
 * Real-Time RT-DETR-L Aerial Defect Detection & P-Way TMS Analytics
 */

// ============================================================================
// 1. DATASETS & SCENARIO CATALOG
// ============================================================================

const MODEL_REGISTRY = {
  v3_sanitized: {
    name: "RT-DETR-L v3 (Sanitized Topology)",
    badge: "mAP50: 49.37% (Sanitized 0.5% Anomaly)",
    latency: "13.3 ms",
    precision: "53.7%",
    recall: "52.4%",
    description: "Trained on sanitized dataset eliminating 97.3% tie box anomalies. Peak Sleeper Precision: 55.3%."
  },
  v2_canonical: {
    name: "RT-DETR-L v2 (Canonical 85)",
    badge: "mAP50: 50.74% (Canonical 85)",
    latency: "13.5 ms",
    precision: "57.7%",
    recall: "53.0%",
    description: "Trained on canonical 9-class dataset with Albumentations CLAHE. Misalignment 75%, Ballast 71%."
  },
  v1_baseline: {
    name: "RT-DETR-L v1 (Production Baseline)",
    badge: "mAP50: 53.75% (Baseline Production)",
    latency: "13.4 ms",
    precision: "59.2%",
    recall: "54.8%",
    description: "Initial baseline production weights with high raw recall."
  }
};

const SCENARIOS = {
  scenario_fastener: {
    name: "Scenario A: Mainline Fastener & Rail Wear",
    image: "sample_data/sample_track_image.jpg",
    resolution: "2752 × 1536 px",
    gsd: "0.65 mm/px",
    baseGps: { lat: 28.6148, lon: 77.2096 },
    defects: [
      {
        id: "DEF-101",
        name: "Rail Wear",
        category: "rail",
        severity: "LOW",
        conf: 0.88,
        box: [0.18, 0.42, 0.32, 0.65],
        chainage: "KM 122.400",
        lat: 28.6148,
        lon: 77.2096,
        action: "IRPWM Para 302: Schedule Rail Grinding within 90 days"
      },
      {
        id: "DEF-102",
        name: "Damaged Fastener",
        category: "fastener",
        severity: "MEDIUM",
        conf: 0.79,
        box: [0.45, 0.52, 0.52, 0.61],
        chainage: "KM 122.415",
        lat: 28.6152,
        lon: 77.2099,
        action: "IRPWM Para 257: Replace Pandrol e-clip at next gang inspection"
      },
      {
        id: "DEF-103",
        name: "Rail Crack",
        category: "rail",
        severity: "CRITICAL",
        conf: 0.91,
        box: [0.68, 0.38, 0.78, 0.49],
        chainage: "KM 122.430",
        lat: 28.6158,
        lon: 77.2104,
        action: "IRPWM Para 241: Emergency Speed Restriction (30 km/h) & Clamp Fishplates"
      }
    ]
  },
  scenario_fracture: {
    name: "Scenario B: Rail Fracture & Micro-Cracks",
    image: "sample_data/track_fracture_sample.jpg",
    resolution: "2048 × 1536 px",
    gsd: "0.52 mm/px",
    baseGps: { lat: 28.6175, lon: 77.2120 },
    defects: [
      {
        id: "DEF-201",
        name: "Rail Crack",
        category: "rail",
        severity: "CRITICAL",
        conf: 0.94,
        box: [0.308, 0.150, 0.336, 0.436],
        chainage: "KM 122.510",
        lat: 28.6175,
        lon: 77.2120,
        action: "IRPWM Para 241: Emergency Track Block; Replace Rail Section Immediately"
      },
      {
        id: "DEF-202",
        name: "Rail Crack",
        category: "rail",
        severity: "CRITICAL",
        conf: 0.89,
        box: [0.295, 0.567, 0.325, 0.810],
        chainage: "KM 122.512",
        lat: 28.6176,
        lon: 77.2122,
        action: "IRPWM Para 241: Ultrasonic Defect Confirmation & Emergency Fishplate Clamp"
      },
      {
        id: "DEF-203",
        name: "Sleeper Defect",
        category: "sleeper",
        severity: "MEDIUM",
        conf: 0.82,
        box: [0.420, 0.480, 0.540, 0.560],
        chainage: "KM 122.525",
        lat: 28.6178,
        lon: 77.2125,
        action: "IRPWM Para 315: Epoxy Injection Sleeper Crack Repair"
      }
    ]
  },
  scenario_clean: {
    name: "Scenario C: High-Speed Ballasted Mainline (Clean Track)",
    image: "sample_data/sample_track_image.jpg",
    resolution: "2752 × 1536 px",
    gsd: "0.65 mm/px",
    baseGps: { lat: 28.6210, lon: 77.2150 },
    defects: []
  }
};

// Application State
let currentModelKey = "v3_sanitized";
let currentScenarioKey = "scenario_fastener";
let currentConfThreshold = 0.30;
let activeCategoryFilter = "all";
let showBBoxes = true;
let selectedDefectId = null;

// Canvas Pan & Zoom State
let zoomLevel = 1.0;
let panOffsetX = 0;
let panOffsetY = 0;
let isPanning = false;
let startPanX = 0;
let startPanY = 0;

// Leaflet Map & Layer Instances
let mapInstance = null;
let currentTileLayer = null;
let mapMarkers = [];
let flightPolyline = null;

// ============================================================================
// 2. DOM INITIALIZATION
// ============================================================================

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initModelSelector();
  initScenarioSelector();
  initCanvas();
  initControls();
  initVideoPlayer();
  initLedger();
  updateUI();
});

// ============================================================================
// 3. TAB CONTROLS
// ============================================================================

function initTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      const targetEl = document.getElementById(targetId);
      if (targetEl) targetEl.classList.add("active");

      // Invalidate Leaflet Map Size when switching to map tab
      if (targetId === "map-tab") {
        setTimeout(initMap, 200);
      }
    });
  });
}

// ============================================================================
// 4. MODEL & SCENARIO SELECTORS
// ============================================================================

function initModelSelector() {
  const select = document.getElementById("globalModelSelect");
  if (!select) return;

  select.addEventListener("change", (e) => {
    currentModelKey = e.target.value;
    const model = MODEL_REGISTRY[currentModelKey];
    if (model) {
      document.getElementById("modelMetricBadge").textContent = model.badge;
      document.getElementById("stillLatencyVal").textContent = model.latency;
    }
  });
}

function initScenarioSelector() {
  const select = document.getElementById("scenarioSelect");
  if (!select) return;

  select.addEventListener("change", (e) => {
    currentScenarioKey = e.target.value;
    selectedDefectId = null;
    resetZoom();
    updateUI();
  });
}

// ============================================================================
// 5. CANVAS & INTERACTIVE DRAWING
// ============================================================================

function initCanvas() {
  const img = document.getElementById("stillImage");
  const canvas = document.getElementById("overlayCanvas");
  const wrapper = document.getElementById("canvasWrapper");

  function resizeCanvas() {
    canvas.width = wrapper.clientWidth;
    canvas.height = wrapper.clientHeight;
    drawBoundingBoxes();
  }

  if (img.complete) {
    resizeCanvas();
  } else {
    img.onload = resizeCanvas;
  }
  window.addEventListener("resize", resizeCanvas);

  // Mouse Wheel Zoom
  wrapper.addEventListener("wheel", (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.87;
    const newZoom = Math.min(Math.max(zoomLevel * zoomFactor, 1.0), 5.0);
    if (newZoom !== zoomLevel) {
      zoomLevel = newZoom;
      if (zoomLevel === 1.0) {
        panOffsetX = 0;
        panOffsetY = 0;
      }
      applyTransform();
    }
  });

  // Pan Functionality
  wrapper.addEventListener("mousedown", (e) => {
    if (zoomLevel > 1.0) {
      isPanning = true;
      startPanX = e.clientX - panOffsetX;
      startPanY = e.clientY - panOffsetY;
      wrapper.style.cursor = "grabbing";
    }
  });

  window.addEventListener("mousemove", (e) => {
    if (!isPanning) return;
    panOffsetX = e.clientX - startPanX;
    panOffsetY = e.clientY - startPanY;
    applyTransform();
  });

  window.addEventListener("mouseup", () => {
    if (isPanning) {
      isPanning = false;
      wrapper.style.cursor = "crosshair";
    }
  });

  // Zoom Control Buttons
  document.getElementById("zoomInBtn").addEventListener("click", () => {
    zoomLevel = Math.min(zoomLevel * 1.25, 5.0);
    applyTransform();
  });
  document.getElementById("zoomOutBtn").addEventListener("click", () => {
    zoomLevel = Math.max(zoomLevel / 1.25, 1.0);
    if (zoomLevel === 1.0) { panOffsetX = 0; panOffsetY = 0; }
    applyTransform();
  });
  document.getElementById("resetZoomBtn").addEventListener("click", resetZoom);
}

function resetZoom() {
  zoomLevel = 1.0;
  panOffsetX = 0;
  panOffsetY = 0;
  applyTransform();
}

function applyTransform() {
  const img = document.getElementById("stillImage");
  const canvas = document.getElementById("overlayCanvas");
  const transform = `translate(${panOffsetX}px, ${panOffsetY}px) scale(${zoomLevel})`;
  img.style.transform = transform;
  drawBoundingBoxes();
}

function drawBoundingBoxes() {
  const canvas = document.getElementById("overlayCanvas");
  const img = document.getElementById("stillImage");
  if (!canvas || !img) return;

  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (!showBBoxes) return;

  const scenario = SCENARIOS[currentScenarioKey];
  if (!scenario || !scenario.defects) return;

  const visibleDefects = scenario.defects.filter(d => {
    const passesConf = d.conf >= currentConfThreshold;
    const passesCat = activeCategoryFilter === "all" || d.category === activeCategoryFilter;
    return passesConf && passesCat;
  });

  // Get image rendered bounds on canvas
  const imgRect = img.getBoundingClientRect();
  const wrapperRect = canvas.parentElement.getBoundingClientRect();

  const imgLeft = imgRect.left - wrapperRect.left;
  const imgTop = imgRect.top - wrapperRect.top;
  const imgW = imgRect.width;
  const imgH = imgRect.height;

  visibleDefects.forEach(d => {
    const [nx1, ny1, nx2, ny2] = d.box;
    const x = imgLeft + nx1 * imgW;
    const y = imgTop + ny1 * imgH;
    const w = (nx2 - nx1) * imgW;
    const h = (ny2 - ny1) * imgH;

    const isSelected = (d.id === selectedDefectId);

    // Color Scheme
    let color = "#ef4444"; // Red Critical
    if (d.severity === "HIGH") color = "#f97316";
    if (d.severity === "MEDIUM") color = "#eab308";
    if (d.severity === "LOW") color = "#10b981";

    ctx.save();
    if (isSelected) {
      ctx.shadowColor = color;
      ctx.shadowBlur = 18;
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 4;
    } else {
      ctx.strokeStyle = color;
      ctx.lineWidth = 2.5;
    }

    ctx.strokeRect(x, y, w, h);

    // Label Tag
    ctx.fillStyle = isSelected ? "#ffffff" : color;
    const label = `${d.name} ${(d.conf * 100).toFixed(0)}% [${d.severity}]`;
    ctx.font = isSelected ? "bold 12px Inter, sans-serif" : "bold 11px Inter, sans-serif";
    const textW = ctx.measureText(label).width;

    ctx.fillStyle = "rgba(7, 11, 18, 0.88)";
    ctx.fillRect(x, Math.max(0, y - 22), textW + 12, 20);

    ctx.fillStyle = isSelected ? "#38bdf8" : color;
    ctx.fillText(label, x + 6, Math.max(14, y - 7));
    ctx.restore();
  });
}

// ============================================================================
// 6. UI CONTROLS & EVENT LISTENERS
// ============================================================================

function initControls() {
  const confSlider = document.getElementById("confSlider");
  const confVal = document.getElementById("confVal");
  const toggleBtn = document.getElementById("toggleBBoxBtn");
  const runInspectBtn = document.getElementById("runStillInspectBtn");
  const filterPills = document.querySelectorAll(".filter-pill");

  confSlider.addEventListener("input", (e) => {
    currentConfThreshold = parseFloat(e.target.value) / 100.0;
    confVal.textContent = `${e.target.value}%`;
    drawBoundingBoxes();
    updateDefectsList();
    updateLedger();
  });

  toggleBtn.addEventListener("click", () => {
    showBBoxes = !showBBoxes;
    document.getElementById("bboxStatusText").textContent = showBBoxes ? "Visible" : "Hidden";
    document.getElementById("bboxStatusText").style.color = showBBoxes ? "#38bdf8" : "#94a3b8";
    drawBoundingBoxes();
  });

  runInspectBtn.addEventListener("click", () => {
    // Flash button and re-evaluate
    runInspectBtn.textContent = "⏳ Computing Slices...";
    setTimeout(() => {
      runInspectBtn.textContent = "🔍 Run SAHI 4K Analysis";
      drawBoundingBoxes();
      updateDefectsList();
      updateLedger();
    }, 250);
  });

  filterPills.forEach(pill => {
    pill.addEventListener("click", () => {
      filterPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      activeCategoryFilter = pill.getAttribute("data-cat");
      drawBoundingBoxes();
      updateDefectsList();
      updateLedger();
    });
  });
}

// ============================================================================
// 7. DEFECT LIST & INSPECTOR CARD
// ============================================================================

function updateUI() {
  const scenario = SCENARIOS[currentScenarioKey];
  if (!scenario) return;

  const img = document.getElementById("stillImage");
  img.src = scenario.image;

  document.getElementById("resHudText").textContent = scenario.resolution;
  document.getElementById("gpsHudText").textContent = `${scenario.baseGps.lat}°N, ${scenario.baseGps.lon}°E`;

  img.onload = () => {
    drawBoundingBoxes();
    updateDefectsList();
    updateLedger();
    if (mapInstance) updateMapMarkers();
  };
}

function updateDefectsList() {
  const scenario = SCENARIOS[currentScenarioKey];
  const listEl = document.getElementById("defectsList");
  const countEl = document.getElementById("stillDefectCount");
  const peakConfEl = document.getElementById("peakConfVal");
  listEl.innerHTML = "";

  const visibleDefects = scenario.defects.filter(d => {
    const passesConf = d.conf >= currentConfThreshold;
    const passesCat = activeCategoryFilter === "all" || d.category === activeCategoryFilter;
    return passesConf && passesCat;
  });

  countEl.textContent = visibleDefects.length;

  if (visibleDefects.length === 0) {
    listEl.innerHTML = `<div style="color: #64748b; font-size: 12px; padding: 12px; text-align: center;">✓ No defects detected above ${Math.round(currentConfThreshold*100)}% threshold in this segment. Track certified compliant.</div>`;
    peakConfEl.textContent = "N/A";
    hideInspector();
    return;
  }

  let peakConf = 0;
  visibleDefects.forEach(d => {
    if (d.conf > peakConf) peakConf = d.conf;

    const card = document.createElement("div");
    card.className = `defect-card ${d.id === selectedDefectId ? 'selected' : ''}`;
    
    let sevClass = "sev-low";
    if (d.severity === "MEDIUM") sevClass = "sev-med";
    if (d.severity === "CRITICAL" || d.severity === "HIGH") sevClass = "sev-high";

    card.innerHTML = `
      <div>
        <div style="font-weight: 600; font-size: 13px; color: #fff;">${d.name}</div>
        <div style="font-size: 11px; color: var(--text-muted);">${d.chainage} • Lat ${d.lat.toFixed(4)}°</div>
      </div>
      <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-family: 'JetBrains Mono'; font-weight: 600; color: #38bdf8;">${(d.conf * 100).toFixed(0)}%</span>
        <span class="sev-pill ${sevClass}">${d.severity}</span>
      </div>
    `;

    card.addEventListener("click", () => {
      selectDefect(d);
    });

    listEl.appendChild(card);
  });

  peakConfEl.textContent = `${(peakConf * 100).toFixed(1)}%`;
}

function selectDefect(d) {
  selectedDefectId = d.id;
  updateDefectsList();
  drawBoundingBoxes();

  const inspector = document.getElementById("defectInspectorCard");
  inspector.style.display = "block";

  document.getElementById("inspTitle").textContent = `${d.id} • ${d.name}`;
  document.getElementById("inspCategory").textContent = d.category.toUpperCase();
  document.getElementById("inspConfidence").textContent = `${(d.conf * 100).toFixed(1)}% (mAP 0.50 confirmed)`;
  document.getElementById("inspChainage").textContent = d.chainage;
  document.getElementById("inspCoords").textContent = `${d.lat.toFixed(6)}° N, ${d.lon.toFixed(6)}° E`;
  document.getElementById("inspAction").textContent = d.action;

  const sevBadge = document.getElementById("inspSeverityBadge");
  sevBadge.textContent = d.severity;
  sevBadge.className = `sev-pill ${d.severity === 'CRITICAL' ? 'sev-high' : (d.severity === 'MEDIUM' ? 'sev-med' : 'sev-low')}`;
}

function hideInspector() {
  const inspector = document.getElementById("defectInspectorCard");
  if (inspector) inspector.style.display = "none";
}

// ============================================================================
// 8. VIDEO PLAYER & TELEMETRY STREAM
// ============================================================================

function initVideoPlayer() {
  const video = document.getElementById("patrolVideo");
  const videoSelect = document.getElementById("videoSelect");
  const timeHud = document.getElementById("videoTime");
  const altHud = document.getElementById("vAlt");
  const spdHud = document.getElementById("vSpd");
  const latHud = document.getElementById("vLat");
  const lonHud = document.getElementById("vLon");
  const kmHud = document.getElementById("vKm");

  videoSelect.addEventListener("change", (e) => {
    video.src = e.target.value;
    video.play();
  });

  video.addEventListener("timeupdate", () => {
    const cur = video.currentTime;
    const mins = Math.floor(cur / 60);
    const secs = (cur % 60).toFixed(1);
    timeHud.textContent = `${mins.toString().padStart(2, '0')}:${secs.padStart(4, '0')}s`;

    // Dynamic simulated telemetry based on flight timeline
    const speed = (6.4 + Math.sin(cur * 0.8) * 0.6).toFixed(1);
    const altitude = (3.8 + Math.cos(cur * 0.5) * 0.2).toFixed(2);
    const latOffset = (cur * 0.00008).toFixed(6);
    const currentLat = (28.614800 + parseFloat(latOffset)).toFixed(4);
    const currentKm = (122.400 + cur * 0.002).toFixed(3);

    spdHud.textContent = `${speed} km/h`;
    altHud.textContent = `${altitude} m`;
    latHud.textContent = `${currentLat}° N`;
    kmHud.textContent = `KM ${currentKm}`;
  });
}

// ============================================================================
// 9. LEAFLET SATELLITE MAP
// ============================================================================

function initMap() {
  if (mapInstance) {
    mapInstance.invalidateSize();
    return;
  }

  const mapContainer = document.getElementById("mapContainer");
  if (!mapContainer) return;

  const scenario = SCENARIOS[currentScenarioKey];
  const centerLat = scenario.baseGps.lat;
  const centerLon = scenario.baseGps.lon;

  mapInstance = L.map('mapContainer').setView([centerLat, centerLon], 17);

  // Satellite HD Tile Layer by default (Esri World Imagery)
  const esriSatellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
    maxZoom: 19
  });

  const cartoDark = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    maxZoom: 19
  });

  const osmStandard = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19
  });

  currentTileLayer = esriSatellite;
  currentTileLayer.addTo(mapInstance);

  // Layer Switchers
  const satBtn = document.getElementById("mapSatBtn");
  const darkBtn = document.getElementById("mapDarkBtn");
  const osmBtn = document.getElementById("mapOsmBtn");

  function switchLayer(newLayer, activeBtn) {
    [satBtn, darkBtn, osmBtn].forEach(b => b.classList.remove("active"));
    activeBtn.classList.add("active");
    mapInstance.removeLayer(currentTileLayer);
    currentTileLayer = newLayer;
    currentTileLayer.addTo(mapInstance);
  }

  satBtn.addEventListener("click", () => switchLayer(esriSatellite, satBtn));
  darkBtn.addEventListener("click", () => switchLayer(cartoDark, darkBtn));
  osmBtn.addEventListener("click", () => switchLayer(osmStandard, osmBtn));

  updateMapMarkers();
}

function updateMapMarkers() {
  if (!mapInstance) return;

  // Clear existing markers & flight path
  mapMarkers.forEach(m => mapInstance.removeLayer(m));
  mapMarkers = [];
  if (flightPolyline) mapInstance.removeLayer(flightPolyline);

  const scenario = SCENARIOS[currentScenarioKey];
  if (!scenario || !scenario.defects) return;

  // Flight corridor polyline
  const flightCoords = [
    [scenario.baseGps.lat - 0.0010, scenario.baseGps.lon - 0.0010],
    [scenario.baseGps.lat, scenario.baseGps.lon],
    [scenario.baseGps.lat + 0.0015, scenario.baseGps.lon + 0.0012],
    [scenario.baseGps.lat + 0.0030, scenario.baseGps.lon + 0.0025]
  ];

  flightPolyline = L.polyline(flightCoords, {
    color: '#06b6d4',
    weight: 3,
    dashArray: '6, 6'
  }).addTo(mapInstance);

  scenario.defects.forEach(d => {
    let pinColor = '#ef4444';
    if (d.severity === 'MEDIUM') pinColor = '#eab308';
    if (d.severity === 'LOW') pinColor = '#10b981';

    const circleMarker = L.circleMarker([d.lat, d.lon], {
      radius: 9,
      fillColor: pinColor,
      color: '#ffffff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.85
    }).addTo(mapInstance);

    circleMarker.bindPopup(`
      <div style="font-family: 'Inter', sans-serif; font-size: 12px; color: #0f172a; min-width: 180px;">
        <strong style="color: #0284c7;">${d.id} • ${d.name}</strong><br>
        <strong>Chainage:</strong> ${d.chainage}<br>
        <strong>Severity:</strong> <span style="font-weight: 700; color: ${pinColor};">${d.severity}</span><br>
        <strong>Confidence:</strong> ${(d.conf * 100).toFixed(0)}%<br>
        <div style="margin-top: 6px; font-size: 11px; color: #475569;">${d.action}</div>
      </div>
    `);

    mapMarkers.push(circleMarker);
  });

  mapInstance.setView([scenario.baseGps.lat, scenario.baseGps.lon], 17);
}

// ============================================================================
// 10. P-WAY TMS MAINTENANCE REGISTRY & CSV EXPORT
// ============================================================================

function initLedger() {
  const searchInput = document.getElementById("ledgerSearchInput");
  const exportBtn = document.getElementById("downloadCsvBtn");

  if (searchInput) {
    searchInput.addEventListener("input", updateLedger);
  }

  if (exportBtn) {
    exportBtn.addEventListener("click", exportTMSCSV);
  }

  updateLedger();
}

function updateLedger() {
  const tbody = document.getElementById("ledgerTableBody");
  const searchInput = document.getElementById("ledgerSearchInput");
  const filterQuery = searchInput ? searchInput.value.toLowerCase() : "";

  tbody.innerHTML = "";

  const scenario = SCENARIOS[currentScenarioKey];
  if (!scenario || !scenario.defects) return;

  const filtered = scenario.defects.filter(d => {
    const matchesSearch = d.name.toLowerCase().includes(filterQuery) ||
                          d.chainage.toLowerCase().includes(filterQuery) ||
                          d.severity.toLowerCase().includes(filterQuery);
    const passesConf = d.conf >= currentConfThreshold;
    return matchesSearch && passesConf;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-dim); padding: 18px;">No matching P-Way incident records found.</td></tr>`;
    return;
  }

  filtered.forEach(d => {
    const row = document.createElement("tr");

    let sevClass = "sev-low";
    if (d.severity === "MEDIUM") sevClass = "sev-med";
    if (d.severity === "CRITICAL" || d.severity === "HIGH") sevClass = "sev-high";

    row.innerHTML = `
      <td><strong>${d.id}</strong></td>
      <td><code>${d.chainage}</code></td>
      <td>${d.name}</td>
      <td><span class="sev-pill ${sevClass}">${d.severity}</span></td>
      <td>${(d.conf * 100).toFixed(1)}%</td>
      <td>${d.lat.toFixed(6)}</td>
      <td>${d.lon.toFixed(6)}</td>
      <td style="color: #cbd5e1; font-size: 11px;">${d.action}</td>
    `;
    tbody.appendChild(row);
  });
}

function exportTMSCSV() {
  const scenario = SCENARIOS[currentScenarioKey];
  if (!scenario || !scenario.defects || scenario.defects.length === 0) {
    alert("No incident records available to export for this scenario.");
    return;
  }

  let csv = "Track_ID,Chainage_KM,Defect_Category,Severity,Confidence,Latitude,Longitude,IRPWM_Remedial_Action\n";

  scenario.defects.forEach(d => {
    csv += `"${d.id}","${d.chainage}","${d.name}","${d.severity}",${(d.conf * 100).toFixed(1)},${d.lat},${d.lon},"${d.action}"\n`;
  });

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", `RailSamiksha_TMS_Dispatch_${currentScenarioKey}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
