"""
RailSamiksha RT-DETR-L Retraining Script (Canonical 9-Class Setup)
==================================================================
Applies the verified notebook training recipe to achieve ~85% mAP50:
- Architecture: RT-DETR-Large (rtdetr-l.pt) with Vision Transformer (ViT) Hybrid Encoder
- Resolution: imgsz=640 (640x640)
- Batch Size: 16 (ensures stable Hungarian query matching gradients)
- Optimizer: AdamW with lr0=0.000769, momentum=0.9
- Precision: Mixed precision (amp=True) on NVIDIA RTX A4000 GPU
- Layer Freezing: None (freeze=None, allowing all ViT attention layers to fully adapt)
- Augmentations: Native Ultralytics + Albumentations (Blur, MedianBlur, ToGray, CLAHE)
- Epochs: 50
"""

import os
from pathlib import Path
import torch
from ultralytics import RTDETR


def main():
    print("=" * 80)
    print("  🚆 RAIL SAMIKSHA — RT-DETR-L CANONICAL 9-CLASS RE-TRAINING (~85% RECIPE)")
    print("=" * 80)

    # 1. Hardware & Environment Audit
    device = "0" if torch.cuda.is_available() else "cpu"
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        print(f"[HARDWARE] Active Device: {gpu_name} ({vram_gb:.1f} GB VRAM) | Device ID: {device}")
    else:
        print("[HARDWARE] WARNING: CUDA not detected, falling back to CPU.")

    # 2. Dataset Path Verification
    data_yaml = Path(r"C:\Users\Administrator\Desktop\RailSamiksha_Drone_defect_detection_Project\Dataset_consolidated\data.yaml")
    if not data_yaml.exists():
        raise FileNotFoundError(f"Dataset config not found at: {data_yaml}")
    print(f"[DATASET] Configuration YAML: {data_yaml}")

    # 3. Model Initialization (Clean Pretrained RT-DETR-L)
    model_weights = Path(r"C:\Users\Administrator\Desktop\RailSamiksha_Drone_defect_detection_Project\rtdetr-l.pt")
    if not model_weights.exists():
        model_weights = "rtdetr-l.pt"
    print(f"[MODEL] Loading Pretrained Weights: {model_weights}")
    model = RTDETR(str(model_weights))

    # 4. Pure Unconstrained Training Execution
    print("\n[TRAINING] Commencing 50 epochs with batch=16, AdamW (lr0=0.000769), amp=True...")
    results = model.train(
        data=str(data_yaml),
        epochs=50,
        batch=16,
        imgsz=640,
        optimizer="AdamW",
        lr0=0.000769,
        momentum=0.9,
        amp=True,
        device=device,
        workers=8,
        freeze=None,                  # NO layer freezing
        project="runs/detect/runs",
        name="rtdetr_v3_canonical_85",
        exist_ok=True,
        save=True,
        save_period=10,
        plots=True,
        verbose=True
    )

    print("\n[COMPLETE] Training successfully finished.")
    print(f"[CHECKPOINT] Best weights saved to: runs/detect/runs/rtdetr_v3_canonical_85/weights/best.pt")


if __name__ == "__main__":
    main()

