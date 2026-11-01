# 🚆 RailSamiksha AI — Enterprise RBAC Aerial Track Inspection Platform

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new)
![Platform](https://img.shields.io/badge/Platform-Vercel%20Edge%20Network-000000?style=flat&logo=vercel)
![Vision Transformer](https://img.shields.io/badge/Architecture-RT--DETR--L-06b6d4?style=flat)
![Security & RBAC](https://img.shields.io/badge/Access%20Control-Authentication%20%26%20RBAC-8b5cf6?style=flat)
![Standards](https://img.shields.io/badge/Compliance-Indian%20Railways%20IRPWM%20TMS-10b981?style=flat)

RailSamiksha AI is an enterprise-grade aerial railway defect inspection platform designed with a **Secure User Authentication & 3-Tier Role-Based Access Control (RBAC)** architecture mirroring Indian Railways operational hierarchies:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               RAILSAMIKSHA ENTERPRISE AUTHENTICATION & RBAC ARCHITECTURE               │
└────────────────────────────────────────────────────────────────────────────────────────┘

    [ SECURE AUTHENTICATION PORTAL (Sign In / Register / Demo 1-Click) ]
                                    │
                                    ▼
    ┌──────────────────────────────────────────────────────────────────────────────┐
    │                        SESSION STORE & RBAC ROUTER                           │
    └──────────────────────────────────────┬───────────────────────────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         ▼                                 ▼                                 ▼
   [ 👑 SUPER ADMIN ]              [ 🎮 DRONE OPERATOR ]          [ 🔧 DEFECT CLEARANCE ]
   • Executive Radar HUD           • 4K SAHI Inspection           • View Dispatched Orders
   • Total Surveys & Live Flights  • Video Patrol Telemetry HUD   • GPS Defect Pinpoint Map
   • Central TMS CSV Repository    • AI BBox Verification         • IRPWM Remedial Punch-List
   • Audit Operator & Gang Views   • Sign & Submit Survey to TMS  • Certify Section Safe (100%)
```

---

## 🔐 Default Demo Accounts (Instant 1-Click Access)

The login screen provides **One-Click Demo Buttons** for instant evaluation without typing passwords, or you can use these credentials:

| Role | Email / Username | Default Password | Official Title & Department |
| :--- | :--- | :---: | :--- |
| 👑 **Super Admin** | `admin@railsamiksha.gov.in` / `superadmin` | `admin123` | Er. Rajesh Singhania (Chief Track Engineer, HQ) |
| 🎮 **Drone Operator** | `operator@railsamiksha.gov.in` / `dronepilot` | `pilot123` | Capt. A. Verma (DGCA Certified Pilot IR-9921) |
| 🔧 **Defect Clearance** | `clearance@railsamiksha.gov.in` / `gang12` | `gang123` | M. Kumar (JE P-Way Gang 12, Agra North) |

> **New User Registration**: Anyone can click the **"Create Account"** tab to register a new account, pick their role, and assign their railway division.

---

## 👥 Three Specialized User Portals

### 1. 👑 Super Admin Platform (Chief Track Engineer - Headquarters)
* **Executive Divisional Radar**:
  * Real-time metrics: Total Surveys Done, Active In-Flight Patrols, Total Identified Defects, and Divisional Clearance Ratio (%).
* **Live Corridor GIS Fleet Map**:
  * Visualizes surveyed corridors with color coding (Green: 100% Cleared, Amber: Pending Remediation, Pulsing Cyan: Active In-Flight Drone).
* **Central TMS CSV Repository**:
  * Master repository of all flight survey records with 1-click **Export Master CSV** compliant with Indian Railways Track Management System (TMS).
* **Admin Audit View Switcher**:
  * Allows HQ admins to audit what the Drone Operator and Field Gang see without logging out.

### 2. 🎮 Drone Operator Platform (Field Pilot & AI Inspector)
* **4K SAHI Inspection Canvas**:
  * High-resolution orthophoto slicing (GSD 0.65 mm/px) with pan and zoom controls.
* **Drone Patrol Video Stream**:
  * Overlaid HUD updating altitude AGL, speed, gimbal pitch, and track chainage.
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
* **"🛡️ Certify Section Defect Clearance Complete"**:
  * Once all defects are marked repaired, unlocks the safety certificate sign-off.
  * Instantly notifies Super Admin, updating the section to **100% Cleared**!

---

## 🚀 Instant Deployment to Vercel

1. Commit and push repository to GitHub:
   ```bash
   git add .
   git commit -m "feat: complete authentication and enterprise RBAC architecture"
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
