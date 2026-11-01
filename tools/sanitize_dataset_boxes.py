"""
RailSamiksha Dataset Topology Sanitizer
========================================
Creates 'Dataset_consolidated_clean' by correcting flawed bounding box annotations:
1. Sleeper Defect (8): Clamps whole-tie macro-boxes (h/w > 0.40) to localized defect zones (<= 0.22).
2. Fasteners (1 & 3): Clamps baseplate-enclosing macro-boxes (> 0.14) to standard clip scale (<= 0.08).
3. Rail Crack (4): Clamps full-frame span boxes (1.00 width) to localized crack regions (<= 0.25).
4. Rail Joint Damage (5): Clamps oversized joint clusters to standard fishplate boundaries (<= 0.25).
5. Rail Wear (7): Clamps extreme full-track streaks to standard segment bounds (<= 0.35).
6. Preserves pristine original Dataset_consolidated as untouched reference.
"""

import os
import shutil
from pathlib import Path
from collections import defaultdict
import numpy as np

SRC_DIR = Path("Dataset_consolidated")
DST_DIR = Path("Dataset_consolidated_clean")

def sanitize_box(cid: int, xc: float, yc: float, bw: float, bh: float):
    """
    Applies strict physical dimension bounds per railway defect category.
    """
    orig_bw, orig_bh = bw, bh
    modified = False

    # Class 8: Sleeper Defect
    if cid == 8:
        # Full vertical tie spanning > 40% of image height
        if bh > 0.35 and bw < 0.15:
            bh = 0.20
            modified = True
        elif bw > 0.35 and bh < 0.15:
            bw = 0.20
            modified = True
        elif bw > 0.35 or bh > 0.35:
            bw = min(0.25, bw)
            bh = min(0.25, bh)
            modified = True
        # Filter sub-pixel noise
        bw = max(0.02, bw)
        bh = max(0.02, bh)

    # Class 1 & 3: Fasteners (Damaged & Missing)
    elif cid in (1, 3):
        # Oversized boxes enclosing entire baseplate or tie
        if bw > 0.12 or bh > 0.12:
            bw = min(0.07, bw)
            bh = min(0.07, bh)
            modified = True
        # Under-sized sub-pixel noise
        if bw < 0.018 or bh < 0.018:
            bw = max(0.025, bw)
            bh = max(0.025, bh)
            modified = True

    # Class 4: Rail Crack
    elif cid == 4:
        # Full-screen span box
        if bw > 0.35:
            bw = 0.20
            modified = True
        if bh > 0.35:
            bh = 0.20
            modified = True

    # Class 5: Rail Joint Damage
    elif cid == 5:
        if bw > 0.30:
            bw = 0.20
            modified = True
        if bh > 0.30:
            bh = 0.20
            modified = True

    # Class 7: Rail Wear
    elif cid == 7:
        if bw > 0.40:
            bw = 0.30
            modified = True
        if bh > 0.40:
            bh = 0.30
            modified = True

    # Ensure coordinates remain strictly inside [0.0, 1.0]
    x1 = max(0.0, xc - bw / 2)
    y1 = max(0.0, yc - bh / 2)
    x2 = min(1.0, xc + bw / 2)
    y2 = min(1.0, yc + bh / 2)
    bw = x2 - x1
    bh = y2 - y1
    xc = (x1 + x2) / 2
    yc = (y1 + y2) / 2

    return cid, xc, yc, bw, bh, modified


def main():
    print("=" * 80)
    print("  [DATASET SANITIZER] Generating Dataset_consolidated_clean...")
    print("=" * 80)

    if DST_DIR.exists():
        print(f"[CLEANUP] Removing previous {DST_DIR}...")
        shutil.rmtree(DST_DIR)

    DST_DIR.mkdir(parents=True, exist_ok=True)

    total_images_copied = 0
    total_boxes_processed = 0
    total_boxes_sanitized = 0
    mods_by_class = defaultdict(int)

    for split in ["train", "valid", "test"]:
        src_img_dir = SRC_DIR / split / "images"
        src_lbl_dir = SRC_DIR / split / "labels"
        dst_img_dir = DST_DIR / split / "images"
        dst_lbl_dir = DST_DIR / split / "labels"

        dst_img_dir.mkdir(parents=True, exist_ok=True)
        dst_lbl_dir.mkdir(parents=True, exist_ok=True)

        img_files = list(src_img_dir.glob("*.jpg")) + list(src_img_dir.glob("*.png"))
        print(f"[PROCESSING] Split '{split}': {len(img_files)} images...")

        for img_p in img_files:
            # Copy image (using hardlink / copy)
            dst_img_p = dst_img_dir / img_p.name
            shutil.copy2(img_p, dst_img_p)
            total_images_copied += 1

            lbl_p = src_lbl_dir / f"{img_p.stem}.txt"
            dst_lbl_p = dst_lbl_dir / f"{img_p.stem}.txt"

            if not lbl_p.exists():
                # Clean background image
                dst_lbl_p.write_text("", encoding="utf-8")
                continue

            lines = lbl_p.read_text(encoding="utf-8").strip().splitlines()
            cleaned_lines = []

            for line in lines:
                parts = line.strip().split()
                if len(parts) < 5:
                    continue

                cid = int(parts[0])
                xc, yc, bw, bh = [float(p) for p in parts[1:5]]
                total_boxes_processed += 1

                cid, n_xc, n_yc, n_bw, n_bh, modified = sanitize_box(cid, xc, yc, bw, bh)

                if modified:
                    total_boxes_sanitized += 1
                    mods_by_class[cid] += 1

                cleaned_lines.append(f"{cid} {n_xc:.6f} {n_yc:.6f} {n_bw:.6f} {n_bh:.6f}")

            dst_lbl_p.write_text("\n".join(cleaned_lines) + "\n", encoding="utf-8")

    # Write data.yaml
    yaml_content = f"""path: {DST_DIR.resolve().as_posix()}
train: { (DST_DIR / 'train' / 'images').resolve().as_posix() }
val: { (DST_DIR / 'valid' / 'images').resolve().as_posix() }
test: { (DST_DIR / 'test' / 'images').resolve().as_posix() }
nc: 9
names:
  0: Ballast Defect
  1: Damaged Fastener
  2: Foreign Objects
  3: Missing Fastener
  4: Rail Crack
  5: Rail Joint Damage
  6: Rail Misalignment
  7: Rail Wear
  8: Sleeper Defect
"""
    (DST_DIR / "data.yaml").write_text(yaml_content, encoding="utf-8")

    print("\n" + "=" * 80)
    print("  SANITIZATION COMPLETE!")
    print("=" * 80)
    print(f"Total Images Processed: {total_images_copied}")
    print(f"Total Bounding Boxes:   {total_boxes_processed}")
    print(f"Total Boxes Sanitized:  {total_boxes_sanitized} ({total_boxes_sanitized/max(1, total_boxes_processed)*100:.1f}%)")
    print("\nSanitized Boxes by Defect Class:")
    names = [
        "Ballast Defect", "Damaged Fastener", "Foreign Objects", "Missing Fastener",
        "Rail Crack", "Rail Joint Damage", "Rail Misalignment", "Rail Wear", "Sleeper Defect"
    ]
    for cid in range(9):
        print(f"  Class {cid} ({names[cid]}): {mods_by_class[cid]} boxes repaired")

    print(f"\nClean Dataset YAML generated at: {(DST_DIR / 'data.yaml').resolve()}")

if __name__ == "__main__":
    main()

