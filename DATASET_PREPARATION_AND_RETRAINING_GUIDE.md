# RailSamiksha — 1,200 to 1,500 Image Dataset Preparation & Retraining Playbook
**Objective**: Scale Railway Defect Detection from **36.25% mAP** to **90%+ Industrial Standard ($\text{mAP}_{50} \ge 85\%\text{--}95\%$)**  
**Target Hardware**: NVIDIA RTX A4000 (16GB VRAM) / Workstation Grade  
**Target Architecture**: RT-DETR-L + SAHI 1:1 Tiling + ByteTrack Temporal Persistence  

---

## 1. Flight Standards & Ground Sample Distance (GSD) Specification

Before collecting imagery, drone flights must adhere strictly to these physical sensor parameters. Inconsistent camera altitude was the primary reason small fastener defects failed in earlier baselines.

| Flight Parameter | Operational Standard | Engineering Purpose |
|---|---|---|
| **Camera Sensor** | 4K UHD ($3840 \times 2160$) or 20MP Mechanical Shutter | Guarantees sub-millimeter pixel detail |
| **Flight Altitude (AGL)** | **3.0 m to 4.5 m above railhead** | Ensures Pandrol clips span $\ge 50\text{--}75\text{px}$ |
| **Ground Sample Distance (GSD)** | **0.6 mm to 0.9 mm per pixel** | Resolves hairline cracks $\ge 1.5\text{mm}$ |
| **Camera Gimbal Angle** | **Strictly 90° Nadir (pure top-down)** | Eliminates 3D perspective distortion |
| **Flight Speed** | **6 km/h to 8 km/h** | Prevents translational motion blur |
| **Shutter Speed** | **$\ge 1/1000\text{s}$ (ISO $\le 400$)** | Eliminates engine vibration blur |
| **Overlap / Stride** | 70% forward overlap if continuous video | Supports multi-frame ByteTrack temporal persistence |

---

## 2. Class-by-Class Image & Annotation Requirements

To achieve **$\ge 90\%$ mAP**, the dataset requires **1,500 raw 4K frames** (~12,000 $640 \times 640$ patches) containing **~10,000 defect annotations**. Below is the exact quota and requirement for every class:

### Detailed Allocation Matrix

| Class ID | Defect Class Name | Target 4K Images | Target BBoxes | Typical Size (Pixels at 4K) | Minimum per Patch |
|:---:|---|:---:|:---:|:---:|:---:|
| **0** | Ballast Defect / Deficiency | **150** | 1,000 | Large ($300 \times 300\text{px}$ to $800 \times 600\text{px}$) | 1–3 boxes |
| **1** | Damaged Fastener | **200** | 1,800 | Micro ($40 \times 40\text{px}$ to $80 \times 80\text{px}$) | 4–8 boxes |
| **2** | Foreign Objects | **100** | 800 | Medium ($80 \times 80\text{px}$ to $300 \times 300\text{px}$) | 1–2 boxes |
| **3** | Missing Fastener | **200** | 1,800 | Micro ($40 \times 40\text{px}$ to $70 \times 70\text{px}$) | 4–8 boxes |
| **4** | Rail Crack | **150** | 1,200 | Linear ($30 \times 60\text{px}$ to $60 \times 250\text{px}$) | 1–3 boxes |
| **5** | Rail Joint Damage | **120** | 800 | Medium ($100 \times 80\text{px}$ to $250 \times 120\text{px}$) | 1–2 boxes |
| **6** | Rail Misalignment | **120** | 600 | Macro ($200 \times 500\text{px}$ to full width) | 1 box |
| **7** | Rail Wear | **110** | 800 | Linear ($40 \times 200\text{px}$ to $80 \times 600\text{px}$) | 1–2 boxes |
| **8** | Broken / Missing Sleeper | **150** | 1,200 | Large ($150 \times 400\text{px}$ to $250 \times 1200\text{px}$) | 1–4 boxes |
| **—** | Clean Track Hard Negatives | **200** | 0 | Whole Frame (Zero Defect Labels) | 0 boxes |
| **TOTAL** | **9 Classes + Hard Negatives** | **1,500** | **~10,000** | **Multi-Scale Envelope** | — |

---

### Per-Class Visual Requirements & Annotation Rules

#### Class 0: Ballast Defect / Deficiency
- **What to Capture**:
  - Track shoulder erosion and washouts where ballast has slumped below the top of sleeper level.
  - Ballast pockets churning into mud / subgrade pump slurry.
  - Excessive loose ballast stones resting on top of the rail head crown.
- **Annotation Rule**:
  - Draw bounding boxes tightly around the depression zone or the ballast heaps on ties. Do not box normal ballast between sleepers.

#### Class 1: Damaged Fastener
- **What to Capture**:
  - Bent or deformed Pandrol e-clips and ERC clips.
  - Severely rusted, cracked, or fractured baseplates.
  - Dislodged rubber rail pads sticking out from beneath the rail foot.
- **Annotation Rule**:
  - Box the individual fastener assembly tightly ($40\text{--}80\text{px}$). Do not include the whole sleeper.

#### Class 2: Foreign Objects
- **What to Capture**:
  - Discarded maintenance tools (spanners, claw bars, grease cans).
  - Fallen branches, rocks, metal scrap, chains, or wire ropes dropped in the four-foot gauge area.
  - Animal carcasses or trash accumulation.
- **Annotation Rule**:
  - Tight bounding box enclosing the object and any distinct shadow that touches it.

#### Class 3: Missing Fastener
- **What to Capture**:
  - Empty sleeper rail seats where a fastener clip has dislodged or fallen out.
  - Unclipped tie plates where only the anchor bolt remains.
  - Missing nylon insulation liners.
- **Annotation Rule**:
  - Box the empty fastener seat where the clip should have been seated. Maintain identical box proportions as a normal clip (~$50 \times 50\text{px}$).

#### Class 4: Rail Crack
- **What to Capture**:
  - Transverse fissures visible on the railhead crown.
  - Head checking and gauge-corner flaking (series of micro hairline fissures).
  - Wheel squat defects and web longitudinal tears.
- **Annotation Rule**:
  - Enclose the fissure with a margin of 5–10 pixels around the crack tips. If micro-cracks form a cluster under 50px apart, group them in one box.

#### Class 5: Rail Joint Damage
- **What to Capture**:
  - Battered and mushroomed rail ends at expansion gaps.
  - Cracked or loose fishplates (joint bars).
  - Missing, loose, or sheared joint bolts.
- **Annotation Rule**:
  - Box the entire fishplate and joint gap assembly, including the bolt holes.

#### Class 6: Rail Misalignment
- **What to Capture**:
  - Heat buckling (lateral snaking kinks in continuously welded rail during hot weather).
  - Localized track gauge widening or gauge narrowing on curves.
  - Track twist and uneven settlement.
- **Annotation Rule**:
  - Box the section of curved rail that deviates from the true parallel track centerline.

#### Class 7: Rail Wear
- **What to Capture**:
  - Rail corrugation (distinct periodic wavy wear pattern on the rail running surface).
  - Wheel burn marks caused by locomotive traction wheelspin.
  - Side wear (shaving of the gauge face on curved track).
- **Annotation Rule**:
  - Box the contiguous worn stripe along the rail crown.

#### Class 8: Broken / Missing Sleeper
- **What to Capture**:
  - Concrete sleeper spalling (exposed steel reinforcement tendons).
  - Full-depth transverse fractures through concrete ties under the rail seat.
  - Rotten or shattered timber ties, or completely missing sleepers.
- **Annotation Rule**:
  - Box the damaged tie section. If the sleeper is split across the center, box the entire sleeper.

#### Clean Track Hard Negatives (Crucial for $\ge 90\%$ Precision)
- **What to Capture (200 Images)**:
  - Complex rail switches, turnouts, frog crossings, and diamond crossings with **zero defects**.
  - Level crossings with rubber or asphalt flangeways.
  - Overhead catenary shadow lines, signal junction boxes, and track lubricators.
- **Annotation Rule**:
  - Create a completely empty `.txt` file for every hard negative frame. This forces the transformer to learn that complex switches and shadows are not defects.

---

## 3. Step-by-Step Dataset Engineering & Retraining Workflow

```
┌─────────────────────────────────┐
│   TASK 1: FLIGHT & INGESTION    │ ───► Capture 1,500 4K frames at 3.0–4.5m AGL
└─────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   TASK 2: QUALITY ANNOTATION    │ ───► Annotate in YOLO format (9 classes + empty txt)
└─────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   TASK 3: PRE-SPLIT DIVISION    │ ───► Split into train (80%), valid (10%), test (10%)
└─────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   TASK 4: OFFLINE SAHI SLICING  │ ───► Run tools/slice_dataset.py -> ~12,000 patches
└─────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   TASK 5: PRODUCTION TRAINING   │ ───► Run train.py with RT-DETR-L on GPU
└─────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   TASK 6: 4K FIELD VALIDATION   │ ───► Run benchmark.py -> Validate >= 90% mAP
└─────────────────────────────────┘
```

---

### Task 1: Ingest Raw 4K Frames into `data_raw/`
1. Export clean 4K frame extractions (`.jpg` or `.png`) from drone video logs.
2. Store raw frames in a staging directory:
   ```
   data_raw/
   ├── 0001_frame.jpg
   ├── 0002_frame.jpg
   ...
   ```

---

### Task 2: Label Annotations in Normalized YOLO Format
Label each defect using any standard annotation software (Label Studio, CVAT, or Roboflow) using standard normalized YOLO format:
```
<class_id> <x_center> <y_center> <width> <height>
```
Where class IDs strictly match [`configs/dataset.yaml`](file:///c:/Users/Administrator/Desktop/RailSamiksha_Drone_defect_detection_Project/configs/dataset.yaml):
- `0`: Ballast Defect
- `1`: Damaged Fastener
- `2`: Foreign Objects
- `3`: Missing Fastener
- `4`: Rail Crack
- `5`: Rail Joint Damage
- `6`: Rail Misalignment
- `7`: Rail Wear
- `8`: Sleeper Defect

---

### Task 3: Divide into Train/Val/Test Splits (BEFORE Slicing)
> [!CRITICAL]
> **Data Leakage Rule**: Always divide the full 4K frames into splits before slicing. Never allow slices from the same 4K flight image to exist in both `train` and `test`.

Structure your raw dataset as:
```
data/
├── train/
│   ├── images/   (1,200 raw 4K images = 80%)
│   └── labels/   (1,200 .txt label files)
├── valid/
│   ├── images/   (150 raw 4K images = 10%)
│   └── labels/   (150 .txt label files)
└── test/
    ├── images/   (150 raw 4K images = 10%)
    └── labels/   (150 .txt label files)
```

---

### Task 4: Execute Offline Slicing Engine
Run the production patch slicer to convert 1,500 4K frames into ~12,000 $640 \times 640$ 1:1 scale patches with hard negative inclusion:

```powershell
.venv\Scripts\python.exe tools/slice_dataset.py `
    --source data `
    --output Dataset_tiled `
    --tile-size 640 `
    --overlap 0.20 `
    --min-box-area-ratio 0.30 `
    --keep-empty-ratio 0.15
```

This generates:
- `Dataset_tiled/train/` (~9,600 patches)
- `Dataset_tiled/valid/` (~1,200 patches)
- `Dataset_tiled/test/` (~1,200 patches)
- `Dataset_tiled/data.yaml`

---

### Task 5: Verify Class Balance
Run the class balancing audit utility to verify that all classes meet the minimum instance requirements:

```powershell
.venv\Scripts\python.exe tools/augment_rare_classes.py `
    --tiled-dir Dataset_tiled `
    --min-instances 300
```

---

### Task 6: Launch Production RT-DETR-L Training
Train the full detection transformer using the production hyperparameter suite:

```powershell
.venv\Scripts\python.exe train.py `
    --data Dataset_tiled/data.yaml `
    --model rtdetr-l.pt `
    --epochs 50 `
    --batch 8 `
    --imgsz 640 `
    --device 0 `
    --name rtdetr_1500_production `
    --save-dir models
```

**Key Hyperparameter Highlights**:
- `close_mosaic=10`: Disables mosaic during the final 10 epochs so the model learns crisp, exact fastener and crack contours without stitch artifacts.
- `box=7.5`, `cls=0.5`, `dfl=1.5`: Optimized loss balance for fine-grained industrial bboxes.
- `cos_lr=True` with AdamW optimizer.

---

### Task 7: Benchmark 4K Field Pipeline
After training completes, verify the full end-to-end 4K inference latency and accuracy:

```powershell
.venv\Scripts\python.exe benchmark.py `
    --model models/rtdetr_1500_production_best.pt `
    --config configs/pipeline_config.yaml `
    --iterations 20
```

---

## 4. Acceptance Criteria for 90%+ Field Certification

Before deploying the weights to the operational drone inspection drone or dashboard ([`app.py`](file:///c:/Users/Administrator/Desktop/RailSamiksha_Drone_defect_detection_Project/app.py)), verify these target metrics on the test split:

| Criterion | Target Metric | Minimum Field Threshold |
|---|:---:|:---:|
| **Overall Model mAP@50** | **$\ge 85.0\% - 92.0\%$** | $80.0\%$ |
| **Overall Model mAP@50-95** | **$\ge 65.0\% - 75.0\%$** | $55.0\%$ |
| **Overall Precision** | **$\ge 90.0\%$** | $85.0\%$ |
| **Fastener Classes (1 & 3) Recall** | **$\ge 85.0\%$** | $80.0\%$ |
| **Rail Crack (Class 4) Recall** | **$\ge 90.0\%$** | $85.0\%$ |
| **4K Frame Latency (RTX A4000)** | **$\le 550\text{ ms}$** | $\le 650\text{ ms}$ |
| **Multi-Frame False-Alarm Rate** | **$< 1.0\%$** (with ByteTrack $N=3$ filter) | $< 2.5\%$ |
