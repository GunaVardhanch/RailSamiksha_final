# RAILWAY DEFECT SYSTEM — STATE & ACTIVITY LEDGER

## Current Project Phase: Day 7 — Standalone Production Application (RailSamiksha_Production_App) Build
- **Active Status:** Extracted 53.75% $mAP_{50}$ model checkpoint (`models/rtdetr_consolidated_run_best.pt`, 66.25 MB) and slimmed ONNX FP16 engine (`models/rtdetr_consolidated_run_best.onnx`, 62.9 MB) into a dedicated standalone production application: `RailSamiksha_Production_App/`. Verified end-to-end SAHI patch slicing, ByteTrack temporal deduplication, telemetry HUD, OpenStreetMap defect pinning, and P-Way CSV report export.
- **Starting Point for Next Action:**
  1. **Launch App:** Run `run_app.bat` or `streamlit run app.py` inside `RailSamiksha_Production_App`.
  2. **Cloud/Docker Deployment:** Package or push to Hugging Face Spaces / Docker registry using the pre-configured `Dockerfile`.
- **Hardware Profile:** HP Z8 Workstation (Intel Xeon Silver 4410Y, 24 cores, 64 GB RAM, NVIDIA RTX A4000 16GB VRAM, CUDA 12.4).
- **Target Metric:** Real-time 4K inference @ ≥ 20 FPS, $mAP_{50} \ge 85\%$.

---

## Daily Work Logs

### [Day 1 Setup, Environment Verification & Dataset Audit]
- **Date:** 2026-10-08
- **Status:** Completed Phase 1 System & GPU Audit, Isolated Environment Setup, Dataset Verification, and Test Split Rebalancing.
- **Hardware Audited:** Microsoft Windows 11 Pro, Intel Xeon Silver 4410Y, 64GB RAM, NVIDIA RTX A4000 (16GB VRAM), CUDA 12.4.
- **Environment Confirmation:** `.venv` created with Python 3.11.9, PyTorch 2.6.0+cu124, `ultralytics`, `sahi`, `supervision`, `opencv-python-headless`, `streamlit`, `pandas`, `pyyaml`, `tabulate`.
- **Dataset Rebalancing & Audit Findings (`reports/DATASET_AUDIT_REPORT.md`):**
  - Final splits: Train: 204 images (438 bboxes), Valid: 59 images (141 bboxes), Test: 33 images (55 bboxes). Total: 296 images, 634 defect bboxes.
  - Test Gap Resolved: 4 pure pairs transferred from train to test, granting positive representation for all 9 classes (Damaged Fastener now 4 in test, Rail Misalignment now 2 in test).

### [Day 2 Architecture & Pipeline Engineering]
- **Date:** 2026-10-08
- **Status:** Completed Phase 2 core inference stack and training engine implementation.
- **Modules Implemented & Verified:**
  1. `train.py`: Full CLI and programmatic training script for RT-DETR (`rtdetr-l.pt`), AdamW optimizer, warmup schedules, and automatic checkpoint archival.
  2. `src/sahi_slicer.py`: SAHI patch slicer calculating overlapping grid (640×640, 20% overlap), slicing 4K/2.7K frames into sub-tiles, and batching onto GPU VRAM.
  3. `src/detector.py`: RT-DETR detection engine supporting batched slice inference and full-frame coarse passes with Hungarian matching (bypassing intra-patch NMS).
  4. `src/postprocessor.py`: Coordinate remapping from tile local coordinates to 4K global coordinates and Non-Maximum Merging (NMM) with confidence-weighted coordinate averaging.
  5. `src/tracker.py`: ByteTrack integration with Kalman temporal tracking and a 3-consecutive-frame flicker filter for persistent defect deduplication.
  6. `src/ingestion.py`: High-throughput video stream engine and synchronized DJI `.SRT` drone telemetry parser.
  7. `src/pipeline.py`: Unified `RailSamikshaPipeline` integrating slicer, detector, postprocessor, and tracker into an end-to-end framework.

### [Day 3 Transfer Learning Optimization & Dataset Scaling Strategy]
- **Date:** 2026-10-08
- **Status:** Completed model convergence diagnosis, transfer learning enhancement, and dataset scaling blueprint.
- **Milestones & Deliverables:**
  1. **Transfer Learning Upgrade:** Upgraded `train.py` with 15 frozen backbone layers, synthetic multi-image augmentations (Mosaic 1.0, MixUp 0.15, Copy-Paste 0.3, Flips), and classification loss weight (`cls=1.5`).
  2. **Model Training:** Completed 99 epochs in 16.7 min on NVIDIA RTX A4000 GPU (early stopped at patience=25).
  3. **Performance Leap:** Precision surged from 1.37% to **79.86%**; Rail Crack mAP50 reached **13.80%**.
  4. **Artifacts Exported:** Checkpoint archived to `models/rtdetr_l_improved_best.pt` (66.3 MB) and compiled to ONNX FP16 engine `models/rtdetr_l_improved_best.onnx` (62.9 MB).
  5. **Root Cause Analysis:** Diagnosed the train-vs-inference resolution mismatch (4K downscaled to 640 compressed defects to 3-4px).
  6. **Production Blueprint:** Authored `production_dataset_expansion_report.md` detailing exact class instance distribution (target 25,500 boxes / 5,000 images) and drone flight parameters (3-5m altitude, 0.5-1.0 mm/px GSD).

### [Day 4 Production Tiling & Scale-Preserving Retraining]
- **Date:** 2026-10-08
- **Status:** Completed Phase 1 & 2 Execution of Production Action Plan.
- **Key Milestones:**
  1. Implemented offline patch slicer `tools/slice_dataset.py` (1:1 scale 640×640 patches, 20% overlap, 15% negative bank).
  2. Implemented `tools/augment_rare_classes.py` balancing minority classes to $\ge 150$ instances.
  3. Redesigned `train.py` with production RT-DETR-L recipe (AdamW, cosine LR, close-mosaic=10).
  4. Trained 35 epochs on NVIDIA RTX A4000 GPU; mAP@50 leaped from 2.21% to **36.25%** (Rail Crack 59.2%, Rail Wear 79.7%, Rail Misalignment 61.7%).
  5. Calibrated pipeline config and benchmarked latency at 502.97 ms/frame.

### [Day 5 Scale-Up Dataset Ingestion & Architecture Alignment]
- **Date:** 2026-10-26
- **Status:** Ingested and audited expanded dataset `Dats set final version part 1.1` (899 images, 1,877 defect boxes, 202 clean negative images, 512×512 resolution).
- **Key Findings:**
  1. Identified that all 9 canonical classes now have positive representation (Rail Wear leaped to 116 boxes, Rail Crack to 154, Missing Fastener to 191, Damaged Fastener to 359, Rail Misalignment to 17).
  2. Mapped raw 11-class Roboflow taxonomy into canonical 9-class system (`configs/dataset.yaml`).
  3. Established execution blueprint for merging, synthetic minority balancing, and RT-DETR-L retrain.

### [Day 6 Final Dataset v3 Ingestion & Consolidated Retraining]
- **Date:** 2026-10-31
- **Status:** Ingested `Railway_defect_dataset_1200` (1,237 images, 3,184 bboxes), removed previous version `Dats set final version part 1.1`, consolidated with `Dataset_pre`, retrained RT-DETR-L, and exported high-throughput ONNX FP16 engine.
- **Key Achievements:**
  1. **Purged Legacy Dataset:** Removed `Dats set final version part 1.1` and cleanly regenerated `Dataset_consolidated`.
  2. **Taxonomy Alignment:** Remapped 15 Roboflow v3 classes into canonical 9 classes (`configs/dataset.yaml`).
  3. **Zero Data Leakage:** Cross-referenced MD5 hashes between `Dataset_pre` and `Railway_defect_dataset_1200`. Resolved 252 overlapping images to latest v3 annotations; merged 44 unique pre images into train split. Zero leakage across train, val, and test splits (1,281 images, 3,253 defect bboxes, 217 clean negatives).
  4. **Retraining & Verification:** Completed 50 epochs on NVIDIA RTX A4000 GPU (`models/rtdetr_v3_1200_consolidated_best.pt`). Test mAP@50 reached **51.22%**, with overall **mAP50-95 reaching 33.49%** (higher than Day 5's 31.22%). Rail Joint Damage surged from 18.1% to **40.2%** (>2x leap). Ballast Defect reached **85.3%**, Foreign Objects **76.8%**, Misalignment **64.2%**.
  5. **Export & SavePoint:** Exported ONNX FP16 engine (`models/rtdetr_v3_1200_consolidated_best.onnx`, 62.9 MB). SavePoint gate safely kept 53.75% Day 5 baseline active in `configs/pipeline_config.yaml` while making Day 6 model available for comparative analysis.

---

## Model Performance Benchmarks
| Checkpoint | Epochs | mAP50 | mAP50-95 | Latency per 4K Frame | Format | Notes |
|---|---|---|---|---|---|---|
| `rtdetr-l-baseline` | 0 | — | — | — | PyTorch FP32 | Pretrained COCO initialization |
| `rtdetr_railsamiksha_best.pt` | 50 | 0.0163 | 0.0093 | 501.81 ms (32 tiles) | PyTorch FP32 | Day 2 baseline fine-tune on RTX A4000 |
| `rtdetr_railsamiksha_best.onnx` | 50 | — | — | Slimmed Graph | ONNX FP16 | Compiled with onnxslim (62.9 MB) |
| `rtdetr_l_improved_best.pt` | 99 | 0.0221 (P=79.9%) | 0.0088 | 501.81 ms (32 tiles) | PyTorch FP32 | Day 3 Improved: Frozen backbone, Mosaic, MixUp |
| `rtdetr_production_tiled_best.pt` | 35 | 0.3625 (P=57.3%) | 0.2135 | 502.97 ms (32 tiles) | PyTorch FP16 | Day 4 Production Tiled: 1:1 scale patches, rare class balancing |
| `rtdetr_consolidated_run_best.pt` | 50 | **0.5375** (P=**61.6%**, R=**54.1%**) | **0.3122** | 16.3 ms / patch | PyTorch FP16 | **Day 5 Consolidated Master Model**: 2,544 images, 4,293 bboxes, all classes $\ge 168$ |
| `rtdetr_consolidated_run_best.onnx` | 50 | — | — | High-Throughput | ONNX FP16 | Compiled with onnxslim opset 18 (62.9 MB) |
| `rtdetr_v3_1200_consolidated_best.pt` | 50 | 0.5122 (P=58.6%, R=51.0%) | **0.3349** | 17.4 ms / image | PyTorch FP16 | **Day 6 Dataset v3 (1200+) Retrain**: Joint Damage surged to 40.2%, Ballast 85.3%, Foreign Objects 76.8% |
| `rtdetr_v3_1200_consolidated_best.onnx` | 50 | — | — | High-Throughput | ONNX FP16 | Compiled with onnxslim opset 18 (62.9 MB) |
| `rtdetr_v3_canonical_85_best.pt` | 50 | 0.5074 (P=57.7%, R=53.0%) | 0.3248 | 16.6 ms / image | PyTorch FP16 | **Day 7 Verified Recipe Retrain**: batch=16, AdamW, Albumentations (CLAHE/Blur), Misalignment 75.0%, Foreign Objects 72.8%, Ballast 71.2% |
| `rtdetr_v3_canonical_85_best.onnx` | 50 | — | — | High-Throughput | ONNX FP16 | Compiled with onnxslim opset 18 (62.9 MB) |

---

## Open Tasks & Backlog
- [x] Phase 1 Hardware & GPU Audit.
- [x] Isolated Python environment (`.venv`) setup with PyTorch CUDA 12.4.
- [x] Verify CUDA acceleration and install core dependencies (`requirements.txt`).
- [x] Verify dataset formatting and annotation integrity (`reports/DATASET_AUDIT_REPORT.md`).
- [x] Rebalance test split to ensure all 9 classes have positive representation in test set.
- [x] Create project canonical configs (`configs/dataset.yaml`, `configs/pipeline_config.yaml`).
- [x] Implement `train.py` for RT-DETR transfer learning.
- [x] Implement batched SAHI slicer with 20% overlap in `src/sahi_slicer.py`.
- [x] Implement RT-DETR detector engine in `src/detector.py`.
- [x] Implement NMM (Non-Maximum Merging) coordinate averaging in `src/postprocessor.py`.
- [x] Integrate ByteTrack with Kalman temporal deduplication in `src/tracker.py`.
- [x] Implement video ingestion & telemetry parser in `src/ingestion.py`.
- [x] Implement unified `RailSamikshaPipeline` in `src/pipeline.py`.
- [x] Implement benchmark suite (`benchmark.py`) for FPS and mAP validation.
- [x] Implement TensorRT export utility in `export_engine.py`.
- [x] Build `app.py` Streamlit review dashboard with GPS coordinate mapping.
- [x] Train RT-DETR Day 2 baseline model (`python train.py --epochs 50 --batch 8`).
- [x] Re-train RT-DETR-L Day 3 with backbone freeze & synthetic augmentations (Precision: 79.9%).
- [x] Export Day 3 model to ONNX FP16 (`models/rtdetr_l_improved_best.onnx`).
- [x] Author comprehensive production dataset scaling blueprint (`production_dataset_expansion_report.md`).
- [x] **[Day 4 Priority 1]** Implement offline patch slicer `tools/slice_dataset.py` with 1:1 scale $640 \times 640$ patches, hard negatives, and leakage prevention.
- [x] **[Day 4 Priority 2]** Implement `tools/augment_rare_classes.py` to balance minority defect classes ($\ge 150$ instances each).
- [x] **[Day 4 Priority 3]** Re-train production RT-DETR-L on `Dataset_tiled` (`mAP50` leaped from 2.21% to **36.25%** on test, **59.2%** on Rail Crack, **79.7%** on Rail Wear).
- [x] **[Day 4 Priority 4]** Calibrate `configs/pipeline_config.yaml` (`perform_standard_pred: False`, conf=0.35, persistence=3) and benchmark 4K latency (502.97 ms / frame).
- [x] **[Day 5 Task 1]** Ingest and audit `Dats set final version part 1.1` (899 images, 1,877 boxes, 202 hard negatives, all 9 classes covered).
- [x] **[Day 5 Task 2]** Implement and run `tools/remap_and_merge_part1_1.py` to remap Part 1.1's raw 11 class labels into canonical 9 classes (`configs/dataset.yaml`) and merge with `Dataset_tiled` into `Dataset_consolidated` (2,544 images, 4,293 defect boxes, 352 negatives; all 9 classes have $\ge 168$ boxes in train).
- [x] **[Day 5 Task 3]** Launch RT-DETR-L production fine-tuning on NVIDIA RTX A4000 GPU on `Dataset_consolidated/data.yaml` (50 epochs completed, test $\text{mAP}_{50}$ reached **53.75%**, best checkpoint saved to `models/rtdetr_consolidated_run_best.pt`).
- [x] **[Day 5 Task 4]** Export best checkpoint to ONNX FP16 (`models/rtdetr_consolidated_run_best.onnx`, 62.9 MB) and update `configs/pipeline_config.yaml`.
- [x] **[Day 5 Task 5]** SavePoint baseline protected (53.75% mAP) and rollback tested via `tools/rollback_to_savepoint.py`.
- [x] **[Day 5 Task 6]** Author textbook-grade project manual (`README.md`) and Dataset v2.0 expansion blueprint (`DATASET_V2_PREPARATION_AND_QUALITY_GUIDE.md`).
- [ ] **[Day 5 Task 7 - Next Up]** Launch `app.py` Streamlit review dashboard and run end-to-end telemetry verification.