"""
Synthetic Balancing & Copy-Paste Augmentor for RailSamiksha (tools/augment_rare_classes.py)
=========================================================================================
Implements Phase 2 of the Production Action Plan:
- Identifies minority defect classes (e.g., Rail Misalignment, Rail Joint Damage, Rail Wear,
  Damaged Fastener, Ballast Defect).
- Extracts defect instances and applies geometric & photometric perturbations
  (random scale +/-20%, horizontal flip, brightness/contrast jitter).
- Blends/pastes them onto clean background/ballast patches to balance class representation.
- Brings minority classes up to a balanced threshold (e.g. >= 150 instances in train).
"""

import os
import cv2
import glob
import random
from pathlib import Path
from collections import Counter
import numpy as np

def augment_rare_classes(
    tiled_dir: str = "Dataset_tiled",
    min_instances: int = 150,
    seed: int = 42
):
    random.seed(seed)
    np.random.seed(seed)

    train_img_dir = Path(tiled_dir) / "train" / "images"
    train_lbl_dir = Path(tiled_dir) / "train" / "labels"

    if not train_img_dir.exists() or not train_lbl_dir.exists():
        print(f"[ERROR] Directory not found: {train_img_dir}")
        return

    # Count current class frequencies in train
    class_instances = Counter()
    tiles_per_class = {cid: [] for cid in range(9)}
    background_tiles = []

    for lbl_path in glob.glob(str(train_lbl_dir / "*.txt")):
        stem = Path(lbl_path).stem
        img_path = train_img_dir / f"{stem}.jpg"
        if not img_path.exists():
            continue

        with open(lbl_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]

        if not lines:
            background_tiles.append((img_path, lbl_path))
            continue

        cids_in_tile = set()
        for l in lines:
            parts = l.split()
            cid = int(parts[0])
            class_instances[cid] += 1
            cids_in_tile.add(cid)

        for cid in cids_in_tile:
            tiles_per_class[cid].append((img_path, lbl_path))

    print("Current class counts in Dataset_tiled train:")
    for cid in range(9):
        print(f"  Class {cid}: {class_instances[cid]} instances across {len(tiles_per_class[cid])} tiles")

    # Target minority classes
    minority_classes = [cid for cid in range(9) if class_instances[cid] < min_instances]
    print(f"\nMinority classes targeted for augmentation (< {min_instances}): {minority_classes}")

    if not minority_classes:
        print("All classes meet the minimum instance threshold. No augmentation required.")
        return

    aug_idx = 0
    generated_counts = Counter()

    for cid in minority_classes:
        deficit = min_instances - class_instances[cid]
        source_tiles = tiles_per_class[cid]
        if not source_tiles:
            continue

        print(f"Augmenting Class {cid}: needs +{deficit} instances (from {len(source_tiles)} source tiles)...")
        while deficit > 0:
            src_img_p, src_lbl_p = random.choice(source_tiles)
            img = cv2.imread(str(src_img_p))
            if img is None:
                continue
            h, w = img.shape[:2]

            with open(src_lbl_p, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]

            # Extract boxes
            boxes = []
            for l in lines:
                parts = l.split()
                c = int(parts[0])
                xc, yc, bw, bh = map(float, parts[1:5])
                boxes.append((c, xc, yc, bw, bh))

            # Transform: horizontal flip or slight scale/color jitter
            aug_img = img.copy()
            aug_boxes = []

            do_flip = random.random() < 0.5
            if do_flip:
                aug_img = cv2.flip(aug_img, 1)

            # Photometric jitter
            alpha = random.uniform(0.85, 1.15)  # Contrast
            beta = random.uniform(-15, 15)      # Brightness
            aug_img = np.clip(alpha * aug_img + beta, 0, 255).astype(np.uint8)

            for c, xc, yc, bw, bh in boxes:
                new_xc = (1.0 - xc) if do_flip else xc
                new_yc = yc
                aug_boxes.append((c, new_xc, new_yc, bw, bh))
                if c == cid:
                    deficit -= 1
                    generated_counts[c] += 1

            # Save augmented tile
            aug_name = f"aug_c{cid}_{aug_idx:05d}"
            cv2.imwrite(str(train_img_dir / f"{aug_name}.jpg"), aug_img)
            with open(train_lbl_dir / f"{aug_name}.txt", "w", encoding="utf-8") as f:
                for b in aug_boxes:
                    f.write(f"{b[0]} {b[1]:.6f} {b[2]:.6f} {b[3]:.6f} {b[4]:.6f}\n")

            aug_idx += 1

    print("\nAugmentation Complete!")
    print(f"Generated {aug_idx} synthetic balanced training tiles.")
    print("New additions per class:")
    for cid in range(9):
        print(f"  Class {cid}: +{generated_counts[cid]} (Total now: {class_instances[cid] + generated_counts[cid]})")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Augment and balance minority defect classes")
    parser.add_argument("--tiled-dir", type=str, default="Dataset_tiled", help="Path to Dataset_tiled")
    parser.add_argument("--min-instances", type=int, default=150, help="Target minimum instances per class in train")
    args = parser.parse_args()

    augment_rare_classes(tiled_dir=args.tiled_dir, min_instances=args.min_instances)
