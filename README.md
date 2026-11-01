# RailSamiksha: Autonomous Aerial Railway Defect Detection System
### *An Industrial-Grade, 4K Drone Inspection Framework Powered by Vision Transformers (RT-DETR), SAHI Tiling, ByteTrack Temporal Filtering, and RTK Telemetry Synchronization*

---

## Table of Contents
1. [Project Overview & Mission](#1-project-overview--mission)
2. [End-to-End System Architecture](#2-end-to-end-system-architecture)
   - [2.1 High-Throughput 4K Video & DJI Telemetry Ingestion](#21-high-throughput-4k-video--dji-telemetry-ingestion)
   - [2.2 Slicing Aided Hyper Inference (SAHI) Patch Engine](#22-slicing-aided-hyper-inference-sahi-patch-engine)
   - [2.3 Real-Time Detection Transformer (RT-DETR)](#23-real-time-detection-transformer-rt-detr)
   - [2.4 Post-Processing & Non-Maximum Merging (NMM)](#24-post-processing--non-maximum-merging-nmm)
   - [2.5 ByteTrack Temporal Deduplication & Flicker Filter](#25-bytetrack-temporal-deduplication--flicker-filter)
   - [2.6 Interactive Streamlit Dashboard & RTK-GPS Geo-Tagging](#26-interactive-streamlit-dashboard--rtk-gps-geo-tagging)
3. [Chronological Engineering Progression & Accuracy Milestones](#3-chronological-engineering-progression--accuracy-milestones)
4. [Anatomy of the 9 Canonical Railway Defect Classes](#4-anatomy-of-the-9-canonical-railway-defect-classes)
5. [In-Depth Root Cause Analysis of System Bottlenecks](#5-in-depth-root-cause-analysis-of-system-bottlenecks)
   - [5.1 The 23× Scale Polarization Problem](#51-the-23-scale-polarization-problem)
   - [5.2 Annotation Contradictions in Sleeper Defect (The 437-Box Flaw)](#52-annotation-contradictions-in-sleeper-defect-the-437-box-flaw)
   - [5.3 Statistical Undersampling in the Test Split](#53-statistical-undersampling-in-the-test-split)
   - [5.4 Why Backbone Freezing Failed on Railway Tracks](#54-why-backbone-freezing-failed-on-railway-tracks)
   - [5.5 Ground Sample Distance (GSD) & Interpolation Blur](#55-ground-sample-distance-gsd--interpolation-blur)
6. [Blueprint for Dataset Version 2.0 (Target: $\ge 85\%\text{--}90\%$ Accuracy)](#6-blueprint-for-dataset-version-20-target-ge-85text--90-accuracy)
   - [6.1 Exact Sample Deficits & Image Quotas](#61-exact-sample-deficits--image-quotas)
   - [6.2 Flight Standards & Optical Sensor Parameters](#62-flight-standards--optical-sensor-parameters)
   - [6.3 Golden Rules of Bounding Box Annotation](#63-golden-rules-of-bounding-box-annotation)
   - [6.4 Train / Valid / Test Split Isolation Strategy](#64-train--valid--test-split-isolation-strategy)
7. [Repository Structure & File Sitemap](#7-repository-structure--file-sitemap)
8. [Production Operational Playbook (Commands & Workflows)](#8-production-operational-playbook-commands--workflows)

---

## 1. Project Overview & Mission

Railway track inspection is a vital safety protocol for modern transportation infrastructure. Traditional manual track walking is hazardous, labor-intensive, and prone to human error, particularly for microscopic hairline cracks, dislodged Pandrol fastener clips, and sub-centimeter track misalignments. 

**RailSamiksha** is an autonomous drone-based computer vision system designed to inspect railway tracks from high-resolution 4K aerial footage at high speeds ($\ge 20$ FPS). 

### Key Engineering Objectives:
* **Detection Standard**: Detect 9 distinct structural track defects spanning multiple physical scales (from $40\text{mm}$ Pandrol clips to $50\text{m}$ heat-buckled track snaking).
* **Speed Standard**: Process 4K Ultra-HD footage at $\le 500\text{ms}$ per full frame ($15\text{--}16\text{ms}$ per patch) on an **NVIDIA RTX A4000 GPU (16GB VRAM)**.
* **Accuracy Target**: Scale mean Average Precision from early baselines ($1.63\%$) to industrial grade ($\ge 85\%\text{--}90\%\text{ mAP}_{50}$).
* **Geo-Referenced Alerts**: Associate every physical defect with sub-meter RTK-GPS coordinates parsed from drone telemetry logs (`.SRT`).

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                RAILSAMIKSHA PIPELINE                                   │
│                                                                                        │
│  4K Aerial Video (3840×2160) + DJI Telemetry (.SRT)                                   │
│       │                                                                                │
│       ▼                                                                                │
│  [SAHI Patch Slicer] ──► 1:1 Scale 640×640 Overlapping Patches (20% overlap)          │
│       │                                                                                │
│       ▼                                                                                │
│  [RT-DETR-L Engine] ──► Bipartite Query-Based Detection (GPU VRAM Batched)            │
│       │                                                                                │
│       ▼                                                                                │
│  [Postprocessor]   ──► Coordinate Un-tiling + Non-Maximum Merging (NMM)               │
│       │                                                                                │
│       ▼                                                                                │
│  [ByteTrack]       ──► Kalman State Estimation + 3-Frame Temporal Flicker Filter       │
│       │                                                                                │
│       ▼                                                                                │
│  [app.py Console]  ──► Geo-Tagged Defect Map, RTK GPS, Severity Classification        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. End-to-End System Architecture

### 2.1 High-Throughput 4K Video & DJI Telemetry Ingestion
- **Module**: `src/ingestion.py`
- Standard drone inspections record 4K UHD video ($3840 \times 2160$ at 29.97 FPS or 60 FPS) accompanied by DJI `.SRT` subtitle tracks.
- The `TelemetryParser` decodes per-frame metadata:
  $$\text{Telemetry Frame} = \{\text{Timestamp}, \text{Latitude}, \text{Longitude}, \text{Altitude (AGL)}, \text{Heading}, \text{Gimbal Pitch}, \text{ISO}, \text{Shutter}\}$$
- Frame timestamps are synchronized with video PTS (Presentation Time Stamps) using microsecond timecodes to ensure that every bounding box has an exact real-world coordinate.

### 2.2 Slicing Aided Hyper Inference (SAHI) Patch Engine
- **Module**: `src/sahi_slicer.py`
- **The Core Problem**: Downscaling a $3840 \times 2160$ image directly to $640 \times 640$ compresses a $40\text{px}$ Pandrol clip down to **$3 \times 3\text{ pixels}$**, obliterating all visual features.
- **The Solution**: SAHI divides the 4K frame into an overlapping grid of native $640 \times 640$ patches:
  $$\text{Horizontal Stride} = W_{\text{slice}} \times (1 - \text{overlap}_w) = 640 \times (1 - 0.20) = 512\text{ px}$$
  $$\text{Vertical Stride} = H_{\text{slice}} \times (1 - \text{overlap}_h) = 640 \times (1 - 0.20) = 512\text{ px}$$
- A 4K frame yields exactly **32 patches** ($8 \times 4$ grid). The patches are packed into a single tensor batch `(8, 3, 640, 640)` on the GPU VRAM, bypassing disk I/O.

### 2.3 Real-Time Detection Transformer (RT-DETR)
- **Module**: `src/detector.py`
- Unlike traditional CNNs that rely on Anchor Boxes and Non-Maximum Suppression (NMS), RT-DETR utilizes an **efficient hybrid encoder** and **query-based Hungarian matching**:
  1. **Backbone**: HGNet-v2 (Hierarchical Gradient Network) extracting multi-scale feature pyramids ($S_3, S_4, S_5$).
  2. **AIFI (Attention-based Intra-scale Feature Interaction)**: Applies self-attention strictly to the highest-level feature map ($S_5$), cutting computational complexity while capturing long-range track geometry.
  3. **CCFM (Cross-scale Convergence Feature Mesh)**: Merges high-level semantic context with low-level high-resolution edge maps.
  4. **Transformer Decoder**: Feeds 300 learnable positional queries into cross-attention heads, predicting final bounding box coordinates and class probabilities simultaneously.

### 2.4 Post-Processing & Non-Maximum Merging (NMM)
- **Module**: `src/postprocessor.py`
- **Coordinate Reconstruction**: Each bounding box in patch local coordinates $(x_t, y_t, w_t, h_t)$ is remapped to 4K global coordinates:
  $$X_{\text{global}} = x_t + X_{\text{patch\_offset}}, \quad Y_{\text{global}} = y_t + Y_{\text{patch\_offset}}$$
- **Non-Maximum Merging (NMM)**: When a defect spans the 20% boundary between two adjacent tiles, standard NMS arbitrarily discards one of the boxes. RailSamiksha's NMM groups overlapping detections $(\text{IoU} \ge 0.50)$ and calculates a **confidence-weighted coordinate centroid**:
  $$\bar{X} = \frac{\sum c_i X_i}{\sum c_i}, \quad \bar{Y} = \frac{\sum c_i Y_i}{\sum c_i}, \quad \bar{W} = \frac{\sum c_i W_i}{\sum c_i}, \quad \bar{H} = \frac{\sum c_i H_i}{\sum c_i}$$

### 2.5 ByteTrack Temporal Deduplication & Flicker Filter
- **Module**: `src/tracker.py`
- Drone video contains camera jitter, motion blur, and vibration. A static single-frame detector will flicker, reporting 30 separate defect alerts for a single cracked sleeper over 1 second of flight.
- **ByteTrack Integration**:
  - Uses an 8-dimensional Kalman filter state vector: $[x, y, a, h, \dot{x}, \dot{y}, \dot{a}, \dot{h}]^T$.
  - Associates both high-confidence and low-confidence detections across successive frames.
  - **3-Hit Flicker Filter**: An alert is only confirmed and logged into the official inspection manifest if the defect is tracked across **at least 3 consecutive frames** ($\ge 100\text{ms}$). Transient glints and floating dust are automatically rejected.

### 2.6 Interactive Streamlit Dashboard & RTK-GPS Geo-Tagging
- **Module**: `app.py`
- Provides an intuitive control console for railway maintenance engineers:
  - Video stream rendering with color-coded bounding boxes and defect labels.
  - Real-time GPS coordinate display and interactive defect maps.
  - Inspection log export (CSV / PDF) with defect class, confidence, timestamp, and track chainage.

---

## 3. Chronological Engineering Progression & Accuracy Milestones

| Phase | Dataset Strategy | Model Architecture | Resolution | Test $\text{mAP}_{50}$ | Precision | Key Findings & Breakthroughs |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **Day 1** | 296 raw 4K images | Baseline setup | — | — | — | Verified NVIDIA RTX A4000 GPU; fixed 0-instance test gap. |
| **Day 2** | Full-frame downscaled | RT-DETR-L baseline | $640 \times 640$ | **1.63%** | 1.37% | **Failure Diagnosis**: 4K-to-640 downscaling crushed micro-defects to 3px. |
| **Day 3** | Full-frame downscaled | 15 Frozen Layers + Mosaic | $640 \times 640$ | **2.21%** | **79.86%** | Precision jumped 58× (false alarms stopped), but recall remained low. |
| **Day 4** | `Dataset_tiled` (1:1 scale patches) | RT-DETR-L (Unfrozen) | $640 \times 640$ | **36.25%** | 57.30% | **Major Breakthrough**: 16.4× mAP surge. Native 1:1 scale solved resolution collapse. |
| **Day 5** | `Dataset_consolidated` (2,544 imgs) | RT-DETR-L Production | $640 \times 640$ | **53.75%** | **61.64%** | **Highest Benchmark**: All 9 classes balanced ($\ge 168$ train boxes). Misalignment hit 74%. |
| **Day 5 Exp** | 800px + 10 Layers Frozen | RT-DETR-L | $800 \times 800$ | 44.08% | 48.26% | **SavePoint Activated**: Proved that freezing backbone breaks long track geometry. |

---

## 4. Anatomy of the 9 Canonical Railway Defect Classes

```
0: Ballast Defect       3: Missing Fastener      6: Rail Misalignment
1: Damaged Fastener     4: Rail Crack            7: Rail Wear
2: Foreign Objects      5: Rail Joint Damage     8: Sleeper Defect
```

```
┌──────────────────┬──────────────────────────┬─────────────────────────────────────────────────┐
│ Defect Class     │ Physical Scale on Track  │ Visual Signature & Safety Hazard                │
├──────────────────┼──────────────────────────┼─────────────────────────────────────────────────┤
│ Ballast Defect   │ Macro (300×300 to 800px) │ Washouts, shoulder erosion, subgrade pumping.  │
│ Damaged Fastener │ Micro (40×40 to 70px)    │ Bent/cracked Pandrol clips, fractured plates.   │
│ Foreign Objects  │ Medium (80×80 to 200px)  │ Tools, scrap metal, fallen branches, stones.    │
│ Missing Fastener │ Micro (40×40 to 60px)    │ Empty tie seats, dislodged clips, unfastened.   │
│ Rail Crack       │ Linear (30×60 to 250px)  │ Transverse fissures, head-checking, squats.     │
│ Rail Joint Damage│ Medium (150×150 to 300px)│ Battered rail ends, loose bolts, fishplates.   │
│ Rail Misalignment│ Macro (Full frame track) │ Heat kinks, lateral track snaking, buckling.    │
│ Rail Wear        │ Linear (40×200 to 600px) │ Side wear on curves, head flattening, metal flow│
│ Sleeper Defect   │ Elongated (100×300px)    │ Cracked, broken, or spalled concrete ties.      │
└──────────────────┴──────────────────────────┴─────────────────────────────────────────────────┘
```

---

## 5. In-Depth Root Cause Analysis of System Bottlenecks

### 5.1 The 23× Scale Polarization Problem
Our bounding box audit revealed that the median area of a Pandrol fastener clip is **$2,790\text{ px}^2$** ($60 \times 60\text{px}$), whereas the median area of a Ballast defect is **$65,844\text{ px}^2$** ($300 \times 270\text{px}$) and a Sleeper defect spans $114 \times 322\text{px}$.
- In anchor-free bipartite loss, the gradients from giant $65,000\text{px}^2$ bounding boxes dwarf the gradient updates from $2,700\text{px}^2$ clips.
- As a consequence, the detector achieves **$68\%\text{--}74\%$** on large defects but plateaus at **$48\%$** on fastener clips.

### 5.2 Annotation Contradictions in Sleeper Defect (The 437-Box Flaw)
Our script isolated **493 extreme aspect-ratio boxes** ($>8:1$ or $<1:8$), of which **437 belonged to Sleeper Defect**.
* **The Contradiction**: One annotator enclosed an entire $550\text{px}$ concrete tie across the rail track for a tiny chip, while another annotator boxed only the $35\text{px}$ chip.
* **The Result**: The network is penalized whenever it predicts a tight box because the ground truth demands an entire sleeper, and vice versa. This caps Sleeper Defect accuracy at **42.6%** despite having 1,101 instances.

### 5.3 Statistical Undersampling in the Test Split
In the held-out test split (202 images):
* **Rail Misalignment**: Only **8 boxes**.
* **Rail Joint Damage**: Only **15 boxes**.
* **Ballast Defect**: Only **17 boxes**.
* **Mathematical Consequence**: Missing just **2 boxes** of Rail Misalignment instantly drops its recall by **$25.0\%$**. This creates extreme metric volatility where the test set is not statistically large enough to reflect true model capability.

### 5.4 Why Backbone Freezing Failed on Railway Tracks
In standard transfer learning, freezing early layers prevents overfitting on small datasets. However, when tested on Day 5:
* **Compact Objects Won**: Damaged Fastener precision leaped to **$72.5\%$** and $\text{mAP}$ reached **$57.4\%$**.
* **Geometric Defects Collapsed**: Rail Misalignment dropped from **$74.2\% \rightarrow 20.0\%$**, and Rail Crack dropped from **$51.4\% \rightarrow 22.4\%$**.
* **The Reason**: COCO pretrained weights have filters for organic, rounded shapes (people, animals, cars). Continuous railway tracks require low-level convolutional filters to adapt to parallel steel rails and directional hairline reflections. Freezing layers 0–9 starved the higher transformer queries of raw metallic edge gradients.

### 5.5 Ground Sample Distance (GSD) & Interpolation Blur
Part 1.1 images were downsampled by Roboflow to $512 \times 512$, whereas tiled frames were $640 \times 640$. When forced to train at $800 \times 800$, PyTorch used bilinear interpolation. For a hairline crack only 1–2 pixels wide, upscaling introduced anti-aliasing blur, turning sharp fractures into fuzzy gray smudges and dropping Rail Crack recall from $50.0\%$ to $33.3\%$.

---

## 6. Blueprint for Dataset Version 2.0 (Target: $\ge 85\%\text{--}90\%$ Accuracy)

### 6.1 Exact Sample Deficits & Image Quotas

To scale from **53.75% to 85%+**, the next dataset version requires **280 to 350 targeted images** (~1,200 new defect boxes):

| Defect Class | Current Boxes | Additional Images Needed | Additional Boxes Needed | Priority | Visual Focus Area |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Rail Joint Damage** | **223** | **+80 to +100** | **+250** | 🔴 **CRITICAL** | Battered ends, cracked joint bars, sheared bolts, joint gaps |
| **Rail Misalignment** | **198** | **+40 to +60** | **+80** | 🔴 **HIGH** | Heat kinks, track snaking, lateral buckle, gauge widening |
| **Rail Crack** | **431** | **+50 to +70** | **+150** | 🟠 **HIGH** | Hairline transverse fissures, wheel squats, head-checking |
| **Damaged Fastener** | **551** | **+40 to +50** | **+300** | 🟠 **MEDIUM** | Bent Pandrol clips, cracked baseplates, dislodged rubber pads |
| **Missing Fastener** | **545** | **+30 to +40** | **+250** | 🟠 **MEDIUM** | Empty sleeper rail seats, dislodged Pandrol clips |
| **Rail Wear** | **296** | **+20 to +30** | **+80** | 🟡 **LOW** | Side gauge wear on curved tracks, metal flow |
| **Ballast Defect** | **333** | **+20 to +30** | **+60** | 🟡 **LOW** | Shoulder washouts, subgrade mud pumping |
| **Foreign Objects** | **615** | **0 to +10** | **+20** | 🟢 **ENOUGH** | Maintenance tools, scrap metal, fallen rocks |
| **Sleeper Defect** | **1,101** | **0 new imgs** | **0 new boxes** | 🔵 **RELABEL** | **Relabel only:** Replace 437 whole-tie boxes with localized crack boxes |
| **Clean Track Negatives** | **352** | **+50 clean imgs** | 0 boxes | ⚪ **ESSENTIAL** | Pristine track, turnouts, switches to suppress false alarms |
| **TOTAL** | **4,293** | **+280 to +350** | **~1,200** | — | **Total Target: ~2,850 images / ~5,500 boxes** |

### 6.2 Flight Standards & Optical Sensor Parameters
All future drone inspection video must strictly adhere to these sensor specifications:
* **Camera Gimbal Angle**: Strictly **90° Nadir (pure top-down)**. Oblique angles induce 3D perspective distortion that ruins Pandrol clip recognition.
* **Flight Altitude (AGL)**: **3.0 m to 4.5 m above railhead**. This guarantees Pandrol clips occupy $\ge 55\text{px}$ width.
* **Ground Sample Distance (GSD)**: **0.5 mm to 0.8 mm per pixel**. Essential to resolve hairline cracks $\ge 1.5\text{mm}$.
* **Shutter Speed**: **$\ge 1/1000\text{ s}$ (Fixed manual shutter)**. Eliminates propeller vibration and drone motion blur.
* **ISO**: **$\le 200\text{--}400$**. Avoids sensor grain noise mimicking cracks.
* **Flight Speed**: **5 km/h to 7 km/h**.

### 6.3 Golden Rules of Bounding Box Annotation
1. **Sleeper Defect Rule**: Box **only the broken concrete section ($40 \times 40\text{px}$ to $80 \times 80\text{px}$)**. Never enclose the entire tie across the tracks.
2. **Fastener Clip Rule**: Box **only the Pandrol e-clip / clip shoulder ($45 \times 45\text{px}$ to $60 \times 60\text{px}$)**. Exclude the massive iron tie plate.
3. **Missing Fastener Rule**: Box the empty rail seat where the clip was seated with identical dimensions to a normal clip.
4. **Rail Joint Rule**: Enclose the full fishplate assembly, the gap, and the bolts.
5. **Rail Crack Rule**: Draw the box with a 5–10px margin around the fissure tips. Group micro-squats within 30px into a single box.

### 6.4 Train / Valid / Test Split Isolation Strategy
* **Split Ratios**: **75% Train**, **15% Validation**, **10% Test**.
* **Pre-Slicing Split**: Slicing must happen **after** splitting full drone videos to guarantee zero parent-scene overlap.
* **Test Split Balance**: Every defect class in the held-out test split must have **at least 35 to 50 bounding boxes** to ensure statistically reliable evaluations.

---

## 7. Repository Structure & File Sitemap

```
RailSamiksha_Drone_defect_detection_Project/
├── configs/
│   ├── dataset.yaml                         # Canonical 9-class definitions and paths
│   └── pipeline_config.yaml                 # SAHI, detector, and tracker configuration
├── src/
│   ├── ingestion.py                         # 4K video ingestion & DJI .SRT telemetry parser
│   ├── sahi_slicer.py                       # 1:1 scale 640x640 patch slicer (20% overlap)
│   ├── detector.py                          # RT-DETR Hungarian-matched inference engine
│   ├── postprocessor.py                     # Global un-tiling & Non-Maximum Merging (NMM)
│   ├── tracker.py                           # ByteTrack Kalman filtering & 3-hit temporal filter
│   └── pipeline.py                          # Unified end-to-end RailSamiksha inference pipeline
├── tools/
│   ├── slice_dataset.py                     # Offline dataset patch slicer with hard negative bank
│   ├── augment_rare_classes.py              # Synthetic copy-paste minority class balancing
│   ├── remap_and_merge_part1_1.py           # Canonical Roboflow 11-to-9 class standardization
│   └── rollback_to_savepoint.py             # One-click recovery utility for Day 5 SavePoint
├── scripts/
│   ├── audit_new_dataset.py                 # Raw batch verification script
│   └── analyze_dataset_deep.py              # Deep statistical bounding box & scale analyzer
├── models/
│   ├── rtdetr_consolidated_run_best.pt      # ACTIVE production checkpoint (53.75% mAP50)
│   ├── rtdetr_consolidated_run_best.onnx    # High-throughput FP16 ONNX engine (62.9 MB)
│   └── savepoints/
│       └── day5_53map_baseline/             # Emergency physical snapshot (weights, configs)
├── reports/
│   └── DATASET_AUDIT_REPORT.md              # Historical Day 1 dataset audit record
├── app.py                                   # Streamlit interactive review dashboard & GPS map
├── benchmark.py                             # Latency and throughput benchmarking suite
├── export_engine.py                         # ONNX / TensorRT FP16 engine compiler
├── train.py                                 # Production RT-DETR-L training engine with SavePoint gate
├── PROJECT_STATE.md                         # Active project ledger and activity tracker
├── project daily log                        # Detailed engineering session work log
├── DATASET_V2_PREPARATION_AND_QUALITY_GUIDE.md # Specification manual for Dataset v2.0
└── README.md                                # Textbook-grade project manual and architecture guide
```

---

## 8. Production Operational Playbook (Commands & Workflows)

### 1. Launch the Interactive Dashboard
To inspect test images, video streams, and live GPS coordinate mapping:
```bash
.venv\Scripts\streamlit.exe run app.py
```

### 2. Run Complete 4K Latency Benchmark
To measure end-to-end latency across all 32 patches on the NVIDIA RTX A4000:
```bash
.venv\Scripts\python.exe benchmark.py
```

### 3. Run the Deep Dataset Audit
To inspect class counts, bounding box dimensions, and scale distributions:
```bash
.venv\Scripts\python.exe scripts/analyze_dataset_deep.py
```

### 4. Emergency Rollback to Day 5 SavePoint (53.75% Baseline)
If any future experimental run fails or corrupts configurations:
```bash
.venv\Scripts\python.exe tools/rollback_to_savepoint.py
```

### 5. Retrain RT-DETR-L on a New Dataset Version
When Dataset v2.0 is assembled:
```bash
.venv\Scripts\python.exe train.py --data Dataset_consolidated/data.yaml --epochs 100 --batch 8 --imgsz 640 --device 0 --name rtdetr_v2_run
```

### 6. Export Checkpoint to High-Throughput ONNX FP16
```bash
.venv\Scripts\python.exe export_engine.py --weights models/rtdetr_consolidated_run_best.pt --format onnx --half
```

---
*Authored by the RailSamiksha AI Research & Drone Engineering Team.*  
*Maintained under Microsoft Windows 11 Pro / HP Z8 Workstation / NVIDIA RTX A4000 (16GB VRAM).*
