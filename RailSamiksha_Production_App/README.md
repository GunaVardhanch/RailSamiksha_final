---
title: RailSamiksha AI - AeroInspect RT-DETR
emoji: 🚆
colorFrom: blue
colorTo: cyan
sdk: streamlit
app_file: app.py
pinned: false
license: mit
---

# 🚆 RailSamiksha AI | AeroInspect RT-DETR Platform

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)
[![RT-DETR-L](https://img.shields.io/badge/Model-RT--DETR--L-blue.svg)](https://github.com/ultralytics/ultralytics)
[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-yellow)](https://huggingface.co/spaces)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

Autonomous aerial drone surveillance and railway track defect identification platform powered by **Fine-Tuned RT-DETR-L**, **SAHI 1:1 Scale Overlapping Patch Slicing**, **ByteTrack Spatial-Temporal Tracking**, and **RTK-GPS Defect Mapping**.

---

## ⚡ Deployment Options

### 1. Local 1-Click Launch (Windows)
Double-click [`run_app.bat`](run_app.bat) or run from terminal:
```powershell
cd RailSamiksha_Production_App
..\.venv\Scripts\python.exe run_app.py
```
Your browser will open automatically to **`http://localhost:8501`**.

---

### 2. Deploy Free on Hugging Face Spaces (Cloud Web App)
You can deploy this as a public or private web app accessible from any device or phone:
1. Go to [huggingface.co/new-space](https://huggingface.co/new-space).
2. Choose a name (e.g. `railsamiksha-ai`), select **Streamlit** as SDK, and choose free hardware.
3. Clone your new Space repository:
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/railsamiksha-ai
   ```
4. Copy all files from `RailSamiksha_Production_App/` into that folder.
5. Push to Hugging Face:
   ```bash
   git add .
   git commit -m "Deploy RailSamiksha AI AeroInspect Platform"
   git push origin main
   ```
*Hugging Face will automatically build the container and provide you with a live shareable URL!*

---

### 3. Deploy via Docker
Build and run anywhere (Linux Server, AWS EC2, GCP, Azure, or Edge Devices):
```bash
docker build -t railsamiksha-ai .
docker run -d -p 8501:8501 --name railsamiksha-app railsamiksha-ai
```
Or using Docker Compose:
```bash
docker compose up -d
```

---

## 🔬 9 Canonical Defect Classes Detected

| Class ID | Defect Category | Default Severity | Visual Indicator |
| :---: | :--- | :---: | :---: |
| **4** | Rail Crack | `CRITICAL` | 🔴 Laser Red |
| **6** | Rail Misalignment | `CRITICAL` | 🔴 Dark Red |
| **5** | Rail Joint Damage | `HIGH` | 🟠 Rose / Orange |
| **3** | Missing Fastener | `HIGH` | 🟠 Vivid Amber |
| **1** | Damaged Fastener | `MEDIUM` | 🟡 Electric Gold |
| **8** | Sleeper Defect | `MEDIUM` | 🔵 Aerospace Blue |
| **2** | Foreign Objects | `MEDIUM` | 🟣 Purple |
| **7** | Rail Wear | `LOW` | 🟢 Emerald Green |
| **0** | Ballast Defect | `LOW` | 🔵 Cyber Cyan |
