# 🚆 RailSamiksha AI — Autonomous Aerial Railway Track Defect Inspection Platform (Web Edition)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new)
![Platform](https://img.shields.io/badge/Platform-Vercel%20Edge%20Network-000000?style=flat&logo=vercel)
![Vision Transformer](https://img.shields.io/badge/Architecture-RT--DETR--L-06b6d4?style=flat)
![P-Way Compliance](https://img.shields.io/badge/Standards-Indian%20Railways%20IRPWM%20TMS-10b981?style=flat)

RailSamiksha AI is an aerospace-grade web platform for autonomous aerial railway track defect inspection. It bridges state-of-the-art **RT-DETR-L (Real-Time DEtection TRansformer)** computer vision with real-world **Indian Railways Permanent Way (P-Way)** track maintenance operations.

---

## ⚡ Key Capabilities

1. **4K SAHI Aerial Defect Inspection (Still Orthophotos)**:
   - Evaluates high-resolution orthophoto slices with GSD down to **0.65 mm/px**.
   - Interactive zoom & pan canvas with real-time bounding box toggling and category filters (*Fasteners, Rails, Sleepers*).
   - Interactive defect inspector displaying **Chainage (KM)**, **RTK-GPS coordinates**, and official **IRPWM remedial action codes** (e.g. *Para 241: Emergency Track Block; Clamp Fishplates*).

2. **Live Flight Patrol Video Stream & ByteTrack HUD**:
   - Stream telemetry synchronized to drone video timestamps.
   - Monitors altitude AGL, drone velocity, camera gimbal pitch (-45°), and track chainage.
   - 3-hit temporal confirmation filter to suppress transient false alarms.

3. **Multi-Layer Satellite GIS Corridor Map (Leaflet.js)**:
   - High-definition satellite imagery (Esri World Imagery) and dark tactical layers.
   - Real RTK-GPS flight paths and color-coded hazard markers (*Red: Critical, Yellow: Medium, Green: Low*).

4. **Permanent Way (P-Way) TMS Maintenance Registry**:
   - Real-time ledger of all detected track anomalies.
   - 1-click **Export TMS CSV** compliant with Indian Railways Track Management System (TMS) data formats.

5. **Multi-Model Checkpoint Registry**:
   - Dynamic model switcher between **v3 Sanitized** (0.5% anomaly rate, peak Sleeper Precision 55.3%), **v2 Canonical-85** (50.74% mAP50), and **v1 Baseline Production** (53.75% mAP50).

---

## 🚀 Instant Deployment to Vercel

### Option 1: Import via Vercel Dashboard (Recommended)

1. Push this repository to your GitHub account:
   ```bash
   git add .
   git commit -m "feat: complete RailSamiksha production stack and Vercel web frontend"
   git push -u origin main
   ```
2. Log into [vercel.com](https://vercel.com).
3. Click **"Add New..."** → **"Project"** and select your GitHub repository.
4. Under **"Root Directory"**, click **Edit** and select:
   ```
   RailSamiksha_Web
   ```
5. Click **"Deploy"**. Vercel will instantly build and deploy your edge inspection application in under 15 seconds!

### Option 2: Deploy via Vercel CLI

If you have Node.js and the Vercel CLI installed:
```bash
cd RailSamiksha_Web
vercel
```

---

## 💻 Local Preview

To preview the web app locally on Windows without installing any dependencies:

### Via Double-Click
Double-click [`start_web_preview.bat`](file:///c:/Users/Administrator/Desktop/RailSamiksha_Drone_defect_detection_Project/RailSamiksha_Web/start_web_preview.bat).

### Via Python
```bash
cd RailSamiksha_Web
python -m http.server 3000
```
Then open [http://localhost:3000](http://localhost:3000) in your web browser.

---

## 📁 Web Project Structure

```
RailSamiksha_Web/
├── index.html               # Semantic HTML5 aerospace glassmorphic UI
├── styles.css               # Glassmorphic dark styling & responsive grid
├── app.js                   # Interactive client-side engine (Canvas, Leaflet, TMS CSV)
├── vercel.json              # Vercel Edge CDN headers, routing & caching rules
├── package.json             # NPM metadata and preview scripts
├── start_web_preview.bat    # Windows 1-click local preview launcher
├── sample_data/             # Embedded sample flight clips and orthophotos
│   ├── sample_track_image.jpg
│   ├── track_fracture_sample.jpg
│   ├── sample_track_flight.mp4
│   └── broken_track_patrol.mp4
└── README.md                # Deployment and documentation guide
```

---

## 🔬 RT-DETR Model Benchmark Summary

| Model Checkpoint | Training Recipe | Test $mAP_{50}$ | Test $mAP_{50-95}$ | Latency (RTX A4000) | Anomaly Rate |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **RT-DETR-L v3 Sanitized** | 50 Epochs, AdamW, Clean Box Scale | **49.37%** | 29.32% | 13.3 ms | **0.5% (97.3% Cleaned)** |
| **RT-DETR-L v2 Canonical-85** | 50 Epochs, AdamW, Albumentations CLAHE | **50.74%** | 32.48% | 13.5 ms | 19.5% |
| **RT-DETR-L v1 Baseline** | Consolidated Run, SGD | **53.75%** | 33.10% | 13.4 ms | 19.5% |

---

## 🛡️ License & Standards
Developed for Indian Railways Track Inspection & Maintenance Operations. Adheres to **IRPWM (Indian Railways Permanent Way Manual)** safety protocols.
