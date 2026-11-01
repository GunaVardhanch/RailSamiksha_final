"""
Rollback Utility: Restore Day 5 SavePoint (53.75% mAP Baseline)
===============================================================
Restores:
  - models/rtdetr_consolidated_run_best.pt
  - models/rtdetr_consolidated_run_best.onnx
  - configs/pipeline_config.yaml
"""

import shutil
from pathlib import Path

SAVEPOINT_DIR = Path("models/savepoints/day5_53map_baseline")

def rollback():
    if not SAVEPOINT_DIR.exists():
        print(f"[ERROR] SavePoint directory does not exist: {SAVEPOINT_DIR}")
        return

    print("==================================================")
    print("TRIGGERING EMERGENCY ROLLBACK TO DAY 5 SAVEPOINT")
    print(f"Source: {SAVEPOINT_DIR}")
    print("==================================================")

    # 1. Restore weights
    src_pt = SAVEPOINT_DIR / "rtdetr_consolidated_run_best.pt"
    dst_pt = Path("models/rtdetr_consolidated_run_best.pt")
    if src_pt.exists():
        shutil.copy2(src_pt, dst_pt)
        print(f"  -> Restored PyTorch model: {dst_pt}")

    # 2. Restore ONNX
    src_onnx = SAVEPOINT_DIR / "rtdetr_consolidated_run_best.onnx"
    dst_onnx = Path("models/rtdetr_consolidated_run_best.onnx")
    if src_onnx.exists():
        shutil.copy2(src_onnx, dst_onnx)
        print(f"  -> Restored ONNX engine: {dst_onnx}")

    # 3. Restore pipeline config
    src_cfg = SAVEPOINT_DIR / "pipeline_config.yaml"
    dst_cfg = Path("configs/pipeline_config.yaml")
    if src_cfg.exists():
        shutil.copy2(src_cfg, dst_cfg)
        print(f"  -> Restored pipeline config: {dst_cfg}")

    print("\n[SUCCESS] Rollback complete! System is restored to Day 5 53.75% mAP baseline.")

if __name__ == "__main__":
    rollback()
