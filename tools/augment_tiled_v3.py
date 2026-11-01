"""
Targeted Minority Augmentation for Dataset_tiled_v3 (tools/augment_tiled_v3.py)
=============================================================================
Brings Rail Misalignment (ID 6) and Rail Wear (ID 7) up to >= 300 instances
in the training split using geometric and photometric perturbations.
"""

import cv2
import random
import glob
from pathlib import Path
from collections import Counter
import numpy as np

def augment_minority_v3(
    dataset_dir: str = "Dataset_tiled_v3",
    min_instances: int = 300,
    seed: int = 42
):
    random.seed(seed)
    np.random.seed(seed)

    train_img_dir = Path(dataset_dir) / "train" / "images"
    train_lbl_dir = Path(dataset_dir) / "train" / "labels"

    # Count current class frequencies in train
    class_instances = Counter()
    tiles_per_class = {cid: [] for cid in range(9)}

    for lbl_p in train_lbl_dir.glob("*.txt"):
        stem = lbl_p.stem
        img_p = train_img_dir / f"{stem}.jpg"
        if not img_p.exists():
            continue

        with open(lbl_p, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]

        cids_in_tile = set()
        for l in lines:
            parts = l.split()
            cid = int(parts[0])
            class_instances[cid] += 1
            cids_in_tile.add(cid)

        for cid in cids_in_tile:
            tiles_per_class[cid].append((img_p, lbl_p))

    print("Current class counts in Dataset_tiled_v3 train:")
    for cid in range(9):
        print(f"  Class {cid}: {class_instances[cid]} instances")

    minority_classes = [cid for cid in range(9) if class_instances[cid] < min_instances]
    print(f"\nTargeting minority classes for augmentation (< {min_instances}): {minority_classes}")

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

        print(f"Augmenting Class {cid}: needs +{deficit} instances...")
        while deficit > 0:
            src_img_p, src_lbl_p = random.choice(source_tiles)
            img = cv2.imread(str(src_img_p))
            if img is None:
                continue

            with open(src_lbl_p, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]

            boxes = []
            for l in lines:
                parts = l.split()
                c = int(parts[0])
                xc, yc, bw, bh = map(float, parts[1:5])
                boxes.append((c, xc, yc, bw, bh))

            aug_img = img.copy()
            aug_boxes = []

            # 50% horizontal flip
            do_flip = random.random() < 0.5
            if do_flip:
                aug_img = cv2.flip(aug_img, 1)

            # Photometric jitter
            alpha = random.uniform(0.88, 1.12)  # Contrast
            beta = random.uniform(-12, 12)       # Brightness
            aug_img = np.clip(alpha * aug_img + beta, 0, 255).astype(np.uint8)

            for c, xc, yc, bw, bh in boxes:
                new_xc = (1.0 - xc) if do_flip else xc
                new_yc = yc
                aug_boxes.append((c, new_xc, new_yc, bw, bh))
                if c == cid:
                    deficit -= 1
                    generated_counts[c] += 1

            aug_name = f"aug_v3_c{cid}_{aug_idx:05d}"
            cv2.imwrite(str(train_img_dir / f"{aug_name}.jpg"), aug_img)
            with open(train_lbl_dir / f"{aug_name}.txt", "w", encoding="utf-8") as f:
                for b in aug_boxes:
                    f.write(f"{b[0]} {b[1]:.6f} {b[2]:.6f} {b[3]:.6f} {b[4]:.6f}\n")

            aug_idx += 1

    print("\nAugmentation Complete!")
    print(f"Generated {aug_idx} balanced training patches.")
    for cid in range(9):
        print(f"  Class {cid}: {class_instances[cid] + generated_counts[cid]} instances (added +{generated_counts[cid]})")

if __name__ == "__main__":
    augment_minority_v3()

