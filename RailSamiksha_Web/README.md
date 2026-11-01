# 🚆 RailSamiksha AI — Enterprise RBAC Aerial Track Inspection Platform

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new)
![Platform](https://img.shields.io/badge/Platform-Vercel%20Edge%20Network-000000?style=flat&logo=vercel)
![Vision Transformer](https://img.shields.io/badge/Architecture-RT--DETR--L-06b6d4?style=flat)
![Security & RBAC](https://img.shields.io/badge/Access%20Control-3--Tier%20RBAC-8b5cf6?style=flat)
![Standards](https://img.shields.io/badge/Compliance-Indian%20Railways%20IRPWM%20TMS-10b981?style=flat)

RailSamiksha AI is an enterprise-grade aerial railway defect inspection platform designed with a **3-Tier Role-Based Access Control (RBAC)** architecture mirroring Indian Railways operational hierarchies:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                      RAILSAMIKSHA ENTERPRISE RBAC ARCHITECTURE                         │
└────────────────────────────────────────────────────────────────────────────────────────┘

    [ USER SELECTOR / ROLE-BASED ACCESS CONTROL (RBAC) ]
    ├─ 👑 SUPER ADMIN (Chief Track Engineer - HQ)
    ├─ 🎮 DRONE OPERATOR (Field Pilot & AI Inspector)
    └─ 🔧 DEFECT CLEARANCE ENGINEER (P-Way Field Gang / Section Engineer)

    ┌──────────────────────────────────────────────────────────────────────────────┐
    │                        SHARED TMS CENTRAL STATE ENGINE                       │
    │   Surveys DB | Live Telemetry Stream | Incident Ledgers | Clearance Audit    │
    └──────────────────────────────────────┬───────────────────────────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         ▼                                 ▼                                 ▼
   [ 🎮 OPERATOR ]                 [ 🔧 CLEARANCE GANG ]              [ 👑 SUPER ADMIN ]
   • Live 4K SAHI Inspection      • View Assigned Survey Reports     • Executive Radar HUD
   • Video Patrol & ByteTrack      • GPS Defect Geolocation Pinpoint  • Total Surveys (Done vs Live)
   • BBox & Confidence Tuning      • Defect Punchlist Triage:         • Active Flight Corridor Stream
   • Verify Defect Alert             [Pending] -> [In Progress] ->    • Central CSV/TMS Repository
   • Click "Sign & Submit to DB"     [Repaired & Cleared]             • Live Clearance Status Monitor
         │                         • Enter Gang ID & Work Notes       • Divisional Safety Scorecard
         │ (Submits Survey)        • Click "Certify Section Cleared"         ▲
         └─────────────────────────────────┬─────────────────────────────────┘
                                           │ (Updates State)
                                           └─────────────────────────────────┘
```

---

## 👥 Three Specialized User Portals

### 1. 👑 Super Admin Platform (Chief Track Engineer - Headquarters)
* **Executive Divisional Radar**:
  * Real-time metrics: Total Surveys Done, Active In-Flight Patrols, Total Identified Defects, and Divisional Clearance Ratio (%).
* **Live Corridor GIS Fleet Map**:
  * Visualizes surveyed corridors with color coding (Green: 100% Cleared, Amber: Pending Remediation, Pulsing Cyan: Active In-Flight Drone).
* **Central TMS CSV Repository**:
  * Master repository of all flight survey records.
  * 1-click **Export Master CSV** compliant with Indian Railways Track Management System (TMS).
* **Model Checkpoint Registry**:
  * Side-by-side benchmark matrix of all 3 RT-DETR-L models (v3 Sanitized, v2 Canonical, v1 Baseline).

### 2. 🎮 Drone Operator Platform (Field Pilot & AI Inspector)
* **4K SAHI Inspection Canvas**:
  * High-resolution orthophoto slicing (GSD 0.65 mm/px).
  * Interactive zoom, pan, and bounding box toggling.
* **Drone Patrol Video Stream**:
  * Real-time telemetry HUD updating altitude AGL, speed, gimbal pitch, and track chainage.
* **Verification & Acceptance**:
  * Pilot verifies each AI-detected bounding box (Confirm Defect or Mark False Alarm).
* **"Accept & Submit Survey to TMS Database"**:
  * Signs off the survey with pilot digital signature, creates official CSV record, and dispatches the work order to the Field Clearance Gang.

### 3. 🔧 Defect Clearance Platform (P-Way Field Gang / Section Engineer)
* **Work Order Dispatch**:
  * Accesses submitted surveys assigned to their maintenance section.
* **Georeferenced Pinpoint Map**:
  * Satellite view showing exact physical GPS coordinates and track chainage for walking inspection crews.
* **Interactive Defect Clearance Punch-List**:
  * Shows required Indian Railways remedial standard (*e.g. IRPWM Para 241: Clamp Fishplates & Replace Rail; Para 257: Replace Pandrol e-clips*).
  * Toggle status: `Pending` ➔ `In Progress` ➔ `✓ Cleared / Repaired`.
* **"Certify Section Defect Clearance Complete"**:
  * Once all defects are marked repaired, unlocks the safety certificate sign-off.
  * Instantly notifies Super Admin, updating the section to **100% Cleared**!

---

## 🚀 Instant Deployment to Vercel

1. Commit and push repository to GitHub:
   ```bash
   git add .
   git commit -m "feat: implement 3-tier enterprise RBAC inspection platform"
   git push -u origin main
   ```
2. Log into [vercel.com](https://vercel.com) and click **"Add New..."** → **"Project"**.
3. Select your GitHub repository.
4. Set **Root Directory** to:
   ```
   RailSamiksha_Web
   ```
5. Click **"Deploy"**. Vercel will deploy your edge application in **under 15 seconds**!

---

## 💻 Local Preview

Run locally on Windows with zero dependencies:
* Double-click [`RailSamiksha_Web\start_web_preview.bat`](file:///c:/Users/Administrator/Desktop/RailSamiksha_Drone_defect_detection_Project/RailSamiksha_Web/start_web_preview.bat), or
* Run:
  ```powershell
  python -m http.server 3000 --directory RailSamiksha_Web
  ```
  and visit `http://localhost:3000`.

---

## 🛡️ Railway Safety Compliance
Designed to adhere to **Indian Railways Permanent Way Manual (IRPWM)** and **Track Management System (TMS)** safety inspection protocols.
