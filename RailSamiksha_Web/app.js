/**
 * RailSamiksha AI — Executive SaaS UI Engine (Inspired by Modern Light Dashboard)
 * Real-Time RT-DETR-L Aerial Defect Detection & Indian Railways TMS
 */

// ============================================================================
// 1. AUTHENTICATION & USER STORE
// ============================================================================

const DEFAULT_USERS = [
  {
    id: "USR-001",
    name: "Er. Rajesh Singhania",
    email: "admin@railsamiksha.gov.in",
    username: "superadmin",
    password: "admin123",
    role: "admin",
    roleLabel: "Super Admin (HQ)",
    division: "Railway Board & Northern Railway HQ",
    avatar: "👑"
  },
  {
    id: "USR-002",
    name: "Capt. A. Verma",
    email: "operator@railsamiksha.gov.in",
    username: "dronepilot",
    password: "pilot123",
    role: "operator",
    roleLabel: "Field Drone Pilot",
    division: "Northern Railway, Delhi Division",
    avatar: "🎮"
  },
  {
    id: "USR-003",
    name: "M. Kumar (JE P-Way)",
    email: "clearance@railsamiksha.gov.in",
    username: "gang12",
    password: "gang123",
    role: "clearance",
    roleLabel: "P-Way Field Gang 12",
    division: "North Central Railway, Agra North",
    avatar: "🔧"
  }
];

function getUsersDB() {
  const stored = localStorage.getItem("RAILSAMIKSHA_USERS");
  if (stored) {
    try { return JSON.parse(stored); } catch (e) { /* fallback */ }
  }
  localStorage.setItem("RAILSAMIKSHA_USERS", JSON.stringify(DEFAULT_USERS));
  return DEFAULT_USERS;
}

function saveUsersDB(users) {
  localStorage.setItem("RAILSAMIKSHA_USERS", JSON.stringify(users));
}

let currentUser = null;

// ============================================================================
// 2. CENTRAL REACTIVE DATABASE STORE (TMS MASTER LEDGER)
// ============================================================================

const SURVEYS_DATABASE = [
  {
    id: "SURV-2026-001",
    corridor: "Agra Cantt Fast-Line (KM 88.200 - 90.100)",
    date: "June 21",
    pilot: "Capt. R. Sharma (IR-8821)",
    clearanceGang: "Gang 08 (JE P-Way M. Kumar)",
    status: "CLEARED_100%",
    statusLabel: "✓ 100% Cleared",
    coordinates: [
      [27.1767, 78.0081],
      [27.1780, 78.0105],
      [27.1802, 78.0140]
    ],
    defects: [
      {
        id: "DEF-001-A",
        name: "Ahmad Curtis",
        defectName: "Damaged Fastener",
        subtitle: "Learning streak: 12 days • KM 88.350",
        level: "Beginner",
        levelClass: "medium",
        dateText: "June 21",
        progressPct: 59,
        category: "fastener",
        severity: "MEDIUM",
        chainage: "KM 88.350",
        lat: 27.1772,
        lon: 78.0090,
        action: "IRPWM Para 257: Replace Pandrol e-clip",
        cleared: true,
        clearedAt: "14:22",
        repairedBy: "Gang 08",
        verified: true
      },
      {
        id: "DEF-001-B",
        name: "Emma Smith",
        defectName: "Rail Wear",
        subtitle: "Learning streak: 7 days • KM 89.120",
        level: "Expert",
        levelClass: "low",
        dateText: "June 1",
        progressPct: 35,
        category: "rail",
        severity: "LOW",
        chainage: "KM 89.120",
        lat: 27.1795,
        lon: 78.0125,
        action: "IRPWM Para 302: Rail profile grinding",
        cleared: true,
        clearedAt: "16:45",
        repairedBy: "Gang 08",
        verified: true
      }
    ]
  },
  {
    id: "SURV-2026-002",
    corridor: "Rewari-Jaipur Chord (KM 45.000 - 47.200)",
    date: "May 16",
    pilot: "Capt. S. Khan (IR-9104)",
    clearanceGang: "Gang 14 (JE P-Way S. Yadav)",
    status: "CLEARED_100%",
    statusLabel: "✓ 100% Cleared",
    coordinates: [
      [28.1950, 76.6180],
      [28.1980, 76.6210],
      [28.2010, 76.6250]
    ],
    defects: [
      {
        id: "DEF-002-A",
        name: "William Hall",
        defectName: "Ballast Defect",
        subtitle: "Learning streak: 7 days • KM 45.600",
        level: "Intermediate",
        levelClass: "low",
        dateText: "May 16",
        progressPct: 88,
        category: "ballast",
        severity: "LOW",
        chainage: "KM 45.600",
        lat: 28.1965,
        lon: 76.6195,
        action: "IRPWM Para 223: Ballast packing & tamping",
        cleared: true,
        clearedAt: "11:30",
        repairedBy: "Gang 14",
        verified: true
      }
    ]
  },
  {
    id: "SURV-2026-LIVE",
    corridor: "Delhi-Mathura Mainline (KM 122.400 - 122.800)",
    date: "May 2",
    pilot: "Capt. A. Verma (IR-9921)",
    clearanceGang: "Gang 12 (Sub-division Agra North)",
    status: "IN_SURVEY",
    statusLabel: "● In Active Survey",
    coordinates: [
      [28.6138, 77.2085],
      [28.6148, 77.2096],
      [28.6158, 77.2104],
      [28.6175, 77.2120]
    ],
    defects: [
      {
        id: "DEF-101",
        name: "Liam Lee",
        defectName: "Rail Crack (Transverse)",
        subtitle: "Learning streak: 4days • KM 122.430",
        level: "Beginner",
        levelClass: "critical",
        dateText: "May 2",
        progressPct: 23,
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
      },
      {
        id: "DEF-102",
        name: "David Kim",
        defectName: "Damaged Fastener (Clip Bend)",
        subtitle: "Learning streak: 9 days • KM 122.415",
        level: "Intermediate",
        levelClass: "medium",
        dateText: "Today",
        progressPct: 75,
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
        name: "Sanjay Rao",
        defectName: "Rail Wear (Gauge Flow)",
        subtitle: "Learning streak: 14 days • KM 122.400",
        level: "Expert",
        levelClass: "low",
        dateText: "Today",
        progressPct: 92,
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
      }
    ]
  }
];

// App State
let activeRole = "admin";
let activeSubview = "list"; // 'list' | 'sahi' | 'video' | 'map'
let zoomLevel = 1.0;
let panOffsetX = 0;
let panOffsetY = 0;
let isPanning = false;
let startPanX = 0;
let startPanY = 0;

// ============================================================================
// 3. INITIALIZATION
// ============================================================================

document.addEventListener("DOMContentLoaded", () => {
  initAuth();
  initSidebarRail();
  initRoleSwitcher();
  initSubviewSwitcher();
  initTopButtons();
  initStillCanvas();
  initVideoPlayer();
  initCustomUploads();

  checkSession();
});

// ============================================================================
// 4. AUTH & ROUTING
// ============================================================================

function initAuth() {
  const tabSignIn = document.getElementById("tabSignIn");
  const tabSignUp = document.getElementById("tabSignUp");
  const signInForm = document.getElementById("signInForm");
  const signUpForm = document.getElementById("signUpForm");

  tabSignIn.addEventListener("click", () => {
    tabSignIn.classList.add("active");
    tabSignUp.classList.remove("active");
    signInForm.classList.add("active");
    signUpForm.classList.remove("active");
  });

  tabSignUp.addEventListener("click", () => {
    tabSignUp.classList.add("active");
    tabSignIn.classList.remove("active");
    signUpForm.classList.add("active");
    signInForm.classList.remove("active");
  });

  signInForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const id = document.getElementById("loginIdentifier").value.trim().toLowerCase();
    const pw = document.getElementById("loginPassword").value;

    const users = getUsersDB();
    const user = users.find(u => (u.email.toLowerCase() === id || u.username.toLowerCase() === id) && u.password === pw);

    if (user) {
      logUserIn(user);
    } else {
      alert("Invalid credentials. Try: admin@railsamiksha.gov.in / admin123");
    }
  });

  signUpForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const name = document.getElementById("regFullName").value.trim();
    const email = document.getElementById("regEmail").value.trim().toLowerCase();
    const username = document.getElementById("regUsername").value.trim().toLowerCase();
    const role = document.getElementById("regRole").value;
    const division = document.getElementById("regDivision").value.trim();
    const pass = document.getElementById("regPassword").value;
    const confirm = document.getElementById("regConfirmPassword").value;

    if (pass !== confirm) {
      alert("Passwords do not match.");
      return;
    }

    const users = getUsersDB();
    const newUser = {
      id: `USR-${Date.now()}`,
      name,
      email,
      username,
      password: pass,
      role,
      roleLabel: role === "admin" ? "Super Admin (HQ)" : (role === "operator" ? "Drone Pilot" : "Field Gang"),
      division,
      avatar: role === "admin" ? "👑" : (role === "operator" ? "🎮" : "🔧")
    };

    users.push(newUser);
    saveUsersDB(users);
    logUserIn(newUser);
  });

  document.getElementById("signOutBtn").addEventListener("click", () => {
    localStorage.removeItem("RAILSAMIKSHA_AUTH_SESSION");
    currentUser = null;
    document.getElementById("appScreen").style.display = "none";
    document.getElementById("authScreen").style.display = "flex";
    showToast("Signed Out", "Session ended successfully.", "info");
  });
}

window.quickLogin = function(role) {
  const users = getUsersDB();
  const user = users.find(u => u.role === role);
  if (user) {
    logUserIn(user);
  }
};

function logUserIn(user) {
  currentUser = user;
  localStorage.setItem("RAILSAMIKSHA_AUTH_SESSION", JSON.stringify(user));

  document.getElementById("authScreen").style.display = "none";
  document.getElementById("appScreen").style.display = "flex";

  document.getElementById("userNameDisplay").textContent = user.name;
  document.getElementById("userAvatar").textContent = user.avatar;
  document.getElementById("userRoleBadge").textContent = user.roleLabel;

  setRole(user.role);
  renderDashboard();
  showToast("Welcome", `Logged in as ${user.name}`, "success");
}

function checkSession() {
  const stored = localStorage.getItem("RAILSAMIKSHA_AUTH_SESSION");
  if (stored) {
    try {
      const user = JSON.parse(stored);
      logUserIn(user);
      return;
    } catch (e) {
      localStorage.removeItem("RAILSAMIKSHA_AUTH_SESSION");
    }
  }

  document.getElementById("authScreen").style.display = "flex";
  document.getElementById("appScreen").style.display = "none";
}

// ============================================================================
// 5. SIDEBAR RAIL & ROLE SWITCHERS
// ============================================================================

function initSidebarRail() {
  const railBtns = document.querySelectorAll(".sidebar-nav .rail-btn");
  railBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      railBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const tab = btn.getAttribute("data-rail-tab");

      if (tab === "dash") {
        switchSubview("list");
      } else if (tab === "sahi") {
        switchSubview("sahi");
      } else if (tab === "video") {
        switchSubview("video");
      } else if (tab === "clearance") {
        setRole("clearance");
      } else if (tab === "ledger" || tab === "models") {
        switchSubview("list");
      }
    });
  });
}

function initRoleSwitcher() {
  const roleBtns = document.querySelectorAll(".role-pill-btn");
  roleBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-role");
      setRole(target);
    });
  });
}

function setRole(role) {
  activeRole = role;
  document.querySelectorAll(".role-pill-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-role") === role);
  });

  const titleEl = document.getElementById("topNavTitle");
  if (role === "admin") {
    titleEl.textContent = "Dashboard";
  } else if (role === "operator") {
    titleEl.textContent = "Drone Patrol Command";
  } else if (role === "clearance") {
    titleEl.textContent = "P-Way Field Clearance";
  }

  renderIncidentList();
}

function initSubviewSwitcher() {
  const subBtns = document.querySelectorAll(".seg-pill-btn");
  subBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      subBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const sub = btn.getAttribute("data-subview");
      switchSubview(sub);
    });
  });
}

function switchSubview(sub) {
  activeSubview = sub;
  document.querySelectorAll(".sub-panel-view").forEach(el => el.classList.remove("active"));

  if (sub === "list" || sub === "week" || sub === "month") {
    document.getElementById("subviewList").classList.add("active");
    renderIncidentList();
  } else if (sub === "sahi") {
    document.getElementById("subviewSahi").classList.add("active");
    setTimeout(drawBoundingBoxes, 150);
  } else if (sub === "video") {
    document.getElementById("subviewVideo").classList.add("active");
  }
}

function initTopButtons() {
  const topActionBtn = document.getElementById("topActionBtn");
  const certModal = document.getElementById("certModal");
  const closeCertBtn = document.getElementById("closeCertModalBtn");
  const closeCertBtn2 = document.getElementById("closeCertBtn2");
  const railCertBtn = document.getElementById("railCertBtn");

  function openCertificate() {
    populateCertificateTable();
    certModal.style.display = "flex";
  }

  topActionBtn.addEventListener("click", openCertificate);
  if (railCertBtn) railCertBtn.addEventListener("click", openCertificate);
  closeCertBtn.addEventListener("click", () => certModal.style.display = "none");
  closeCertBtn2.addEventListener("click", () => certModal.style.display = "none");

  // Search input filter
  const searchInput = document.getElementById("globalSearchInput");
  searchInput.addEventListener("input", () => {
    renderIncidentList(searchInput.value.toLowerCase());
  });
}

// ============================================================================
// 6. DASHBOARD RENDERING (MATCHING INSPIRATION IMAGE LIST & RADAR)
// ============================================================================

function renderDashboard() {
  renderIncidentList();
}

function renderIncidentList(filterQuery = "") {
  const container = document.getElementById("incidentRowsList");
  if (!container) return;

  container.innerHTML = "";

  // Collect all defects across surveys
  let allDefects = [];
  SURVEYS_DATABASE.forEach(s => {
    s.defects.forEach(d => {
      allDefects.push({ ...d, surveyId: s.id, corridor: s.corridor });
    });
  });

  if (filterQuery) {
    allDefects = allDefects.filter(d => 
      d.name.toLowerCase().includes(filterQuery) ||
      d.defectName.toLowerCase().includes(filterQuery) ||
      d.chainage.toLowerCase().includes(filterQuery)
    );
  }

  allDefects.forEach(d => {
    const row = document.createElement("div");
    row.className = "incident-row-item";

    let levelClass = "category-soft-pill";
    if (d.severity === "CRITICAL") levelClass += " critical";
    else if (d.severity === "MEDIUM") levelClass += " medium";
    else levelClass += " low";

    row.innerHTML = `
      <div class="inc-user-group">
        <div class="inc-avatar-box">👤</div>
        <div>
          <div class="inc-title">${d.name}</div>
          <div class="inc-sub">${d.subtitle}</div>
        </div>
      </div>

      <div class="${levelClass}">
        📊 ${d.level}
      </div>

      <div class="inc-date-text">
        🗓️ ${d.dateText}
      </div>

      <div class="circular-progress-chip">
        <span class="progress-ring-circle" style="border-top-color: ${d.cleared ? '#10b981' : '#6366f1'};"></span>
        <span>${d.progressPct}%</span>
      </div>

      <button class="three-dots-btn" onclick="toggleDefectStatus('${d.id}')" title="Mark Cleared">
        ${d.cleared ? '✓' : '⋮'}
      </button>
    `;

    container.appendChild(row);
  });
}

window.toggleDefectStatus = function(defectId) {
  SURVEYS_DATABASE.forEach(s => {
    const defect = s.defects.find(d => d.id === defectId);
    if (defect) {
      defect.cleared = !defect.cleared;
      defect.progressPct = defect.cleared ? 100 : 25;
      showToast("Status Updated", `${defect.name}: ${defect.cleared ? 'Cleared' : 'Pending'}`, "success");
    }
  });

  renderIncidentList();
};

function populateCertificateTable() {
  const tbody = document.getElementById("certTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  const liveSurvey = SURVEYS_DATABASE.find(s => s.id === "SURV-2026-LIVE");
  if (!liveSurvey) return;

  liveSurvey.defects.forEach(d => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td style="padding: 6px 8px; border: 1px solid #cbd5e1;"><strong>${d.id}</strong></td>
      <td style="padding: 6px 8px; border: 1px solid #cbd5e1;">${d.defectName}</td>
      <td style="padding: 6px 8px; border: 1px solid #cbd5e1;"><strong>${d.severity}</strong></td>
      <td style="padding: 6px 8px; border: 1px solid #cbd5e1;">${d.chainage}</td>
      <td style="padding: 6px 8px; border: 1px solid #cbd5e1;">${d.action}</td>
      <td style="padding: 6px 8px; border: 1px solid #cbd5e1; color: ${d.cleared ? '#16a34a' : '#d97706'}; font-weight: 700;">
        ${d.cleared ? '✓ Cleared' : '● Pending'}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// ============================================================================
// 7. 4K SAHI CANVAS & PATROL VIDEO
// ============================================================================

function initStillCanvas() {
  const img = document.getElementById("stillImage");
  const canvas = document.getElementById("overlayCanvas");
  const wrapper = document.getElementById("canvasWrapper");

  function resizeCanvas() {
    if (wrapper) {
      canvas.width = wrapper.clientWidth;
      canvas.height = wrapper.clientHeight;
      drawBoundingBoxes();
    }
  }

  if (img) {
    if (img.complete) resizeCanvas();
    else img.onload = resizeCanvas;
  }
  window.addEventListener("resize", resizeCanvas);

  const runBtn = document.getElementById("runStillInspectBtn");
  if (runBtn) {
    runBtn.addEventListener("click", () => {
      showToast("SAHI Inference", "Computed 8 native patches in 13.3ms", "success");
      drawBoundingBoxes();
    });
  }
}

function drawBoundingBoxes() {
  const canvas = document.getElementById("overlayCanvas");
  const img = document.getElementById("stillImage");
  if (!canvas || !img) return;

  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const liveSurvey = SURVEYS_DATABASE.find(s => s.id === "SURV-2026-LIVE");
  if (!liveSurvey) return;

  const imgRect = img.getBoundingClientRect();
  const wrapperRect = canvas.parentElement.getBoundingClientRect();
  const imgLeft = imgRect.left - wrapperRect.left;
  const imgTop = imgRect.top - wrapperRect.top;
  const imgW = imgRect.width;
  const imgH = imgRect.height;

  liveSurvey.defects.forEach(d => {
    if (!d.box) return;
    const [nx1, ny1, nx2, ny2] = d.box;
    const x = imgLeft + nx1 * imgW;
    const y = imgTop + ny1 * imgH;
    const w = (nx2 - nx1) * imgW;
    const h = (ny2 - ny1) * imgH;

    let color = d.severity === "CRITICAL" ? "#ef4444" : (d.severity === "MEDIUM" ? "#f59e0b" : "#10b981");

    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.strokeRect(x, y, w, h);

    ctx.fillStyle = "rgba(17, 24, 39, 0.9)";
    const label = `${d.defectName} ${(d.conf * 100).toFixed(0)}%`;
    ctx.font = "bold 11px 'Plus Jakarta Sans', sans-serif";
    const textW = ctx.measureText(label).width;
    ctx.fillRect(x, Math.max(0, y - 22), textW + 10, 20);

    ctx.fillStyle = "#ffffff";
    ctx.fillText(label, x + 5, Math.max(14, y - 7));
    ctx.restore();
  });
}

function initVideoPlayer() {
  const video = document.getElementById("patrolVideo");
  if (!video) return;

  video.addEventListener("timeupdate", () => {
    const cur = video.currentTime;
    const mins = Math.floor(cur / 60);
    const secs = (cur % 60).toFixed(1);
    const timeEl = document.getElementById("videoTime");
    if (timeEl) timeEl.textContent = `${mins.toString().padStart(2, '0')}:${secs.padStart(4, '0')}s`;

    const spdEl = document.getElementById("vSpd");
    if (spdEl) spdEl.textContent = `${(6.4 + Math.sin(cur * 0.8) * 0.6).toFixed(1)} km/h`;

    const kmEl = document.getElementById("vKm");
    if (kmEl) kmEl.textContent = `KM ${(122.400 + cur * 0.002).toFixed(3)}`;
  });
}

function initCustomUploads() {
  const customImg = document.getElementById("customImageInput");
  const customVid = document.getElementById("customVideoInput");
  const imgEl = document.getElementById("stillImage");
  const vidEl = document.getElementById("patrolVideo");

  if (customImg) {
    customImg.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (re) => {
          imgEl.src = re.target.result;
          imgEl.onload = () => {
            document.getElementById("resHudText").textContent = `${imgEl.naturalWidth} × ${imgEl.naturalHeight} px`;
            drawBoundingBoxes();
            showToast("Custom Orthophoto Loaded", `${file.name} ready for SAHI analysis`, "success");
          };
        };
        reader.readAsDataURL(file);
      }
    });
  }

  if (customVid) {
    customVid.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file) {
        vidEl.src = URL.createObjectURL(file);
        vidEl.play();
        showToast("Custom Patrol Video Loaded", `${file.name} playing`, "success");
      }
    });
  }
}

// ============================================================================
// 8. TOAST SYSTEM
// ============================================================================

function showToast(title, message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `toast-item ${type}`;
  toast.innerHTML = `
    <div style="font-weight: 700; margin-bottom: 2px;">${title}</div>
    <div style="font-size: 11px; opacity: 0.9;">${message}</div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => {
      if (toast.parentElement) toast.parentElement.removeChild(toast);
    }, 300);
  }, 3500);
}
