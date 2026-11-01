"""
Remap & Merge Railway Defect Dataset 1200 with Pre Dataset
(tools/remap_and_merge_v3_1200.py)
==========================================================
Merges:
  1. Railway_defect_dataset_1200 (authoritative final dataset v3, 1,237 images, 15 Roboflow classes)
  2. Dataset_pre (original pre-dataset, preserving unique non-overlapping field images)
into:
  Dataset_consolidated (strictly standardized 9-class dataset ready for RT-DETR-L training)

Class Mapping:
  Raw 0, 1, 2, 3 ('Ballast Deficiency' / 'Defect' / 'Washout') -> Canonical 0 (Ballast Defect)
  Raw 6          ('Damaged Fastener')                          -> Canonical 1 (Damaged Fastener)
  Raw 7          ('Foreign Objects')                           -> Canonical 2 (Foreign Objects)
  Raw 9          ('Missing Fastener')                          -> Canonical 3 (Missing Fastener)
  Raw 10         ('Rail Crack')                                -> Canonical 4 (Rail Crack)
  Raw 11         ('Rail Joint Damage')                         -> Canonical 5 (Rail Joint Damage)
  Raw 12         ('Rail Misalignment')                         -> Canonical 6 (Rail Misalignment)
  Raw 13         ('Rail Wear')                                 -> Canonical 7 (Rail Wear)
  Raw 4, 5, 8, 14 ('Broken/Missing Sleeper', 'Sleeper Defect') -> Canonical 8 (Sleeper Defect)
"""

import os
import shutil
import hashlib
import argparse
from pathlib import Path
from collections import Counter, defaultdict
import yaml

RAW15_TO_CANONICAL = {
    0: 0,   # Ballast  Deficiency -> Ballast Defect
    1: 0,   # Ballast Defect -> Ballast Defect
    2: 0,   # Ballast Deficiency -> Ballast Defect
    3: 0,   # Ballast Washout -> Ballast Defect
    4: 8,   # Broken - Missing Sleeper -> Sleeper Defect
    5: 8,   # Broken Sleeper -> Sleeper Defect
    6: 1,   # Damaged Fastener -> Damaged Fastener
    7: 2,   # Foreign Objects -> Foreign Objects
    8: 8,   # Missing  Sleeper -> Sleeper Defect
    9: 3,   # Missing Fastener -> Missing Fastener
    10: 4,  # Rail Crack -> Rail Crack
    11: 5,  # Rail Joint Damage -> Rail Joint Damage
    12: 6,  # Rail Misalignment -> Rail Misalignment
    13: 7,  # Rail Wear -> Rail Wear
    14: 8,  # Sleeper Defect -> Sleeper Defect
}

CANONICAL_NAMES = [
    "Ballast Defect",
    "Damaged Fastener",
    "Foreign Objects",
    "Missing Fastener",
    "Rail Crack",
    "Rail Joint Damage",
    "Rail Misalignment",
    "Rail Wear",
    "Sleeper Defect",
]

def compute_md5(file_path: Path) -> str:
    return hashlib.md5(file_path.read_bytes()).hexdigest()

def remap_and_merge(
    v3_dir: str = "Railway_defect_dataset_1200",
    pre_dir: str = "Dataset_pre",
    dest_dir: str = "Dataset_consolidated"
):
    v3_path = Path(v3_dir).resolve()
    pre_path = Path(pre_dir).resolve()
    dest_path = Path(dest_dir).resolve()

    print("=" * 70)
    print("RAILSAMIKSHA CANONICAL DATASET CONSOLIDATION (VERSION 3 + PRE DATASET)")
    print(f"Source 1 (New Final Version v3): {v3_path}")
    print(f"Source 2 (Pre Dataset):          {pre_path}")
    print(f"Destination Target Directory:    {dest_path}")
    print("=" * 70)

    splits = ["train", "valid", "test"]

    # Recreate destination directories
    if dest_path.exists():
        print(f"\n[1/5] Target directory {dest_path} already exists. Cleaning up...")
        shutil.rmtree(dest_path)

    for split in splits:
        (dest_path / split / "images").mkdir(parents=True, exist_ok=True)
        (dest_path / split / "labels").mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------
    # Step 2: Index Railway_defect_dataset_1200 MD5 Hashes
    # ----------------------------------------------------
    print("\n[2/5] Ingesting and Remapping Railway_defect_dataset_1200 (15 -> 9 Classes)...")
    v3_hashes = {}
    v3_stats = {s: {"images": 0, "boxes": 0, "empty": 0} for s in splits}

    for split in splits:
        src_img_dir = v3_path / split / "images"
        src_lbl_dir = v3_path / split / "labels"
        dst_img_dir = dest_path / split / "images"
        dst_lbl_dir = dest_path / split / "labels"

        if not src_img_dir.exists():
            print(f"  [Warning] Missing {src_img_dir}")
            continue

        for img_file in src_img_dir.glob("*.*"):
            if img_file.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
                continue

            md5_val = compute_md5(img_file)
            v3_hashes[md5_val] = (split, img_file.name)

            new_stem = f"v3_{img_file.stem}"
            dst_img_path = dst_img_dir / f"{new_stem}{img_file.suffix.lower()}"
            shutil.copy2(img_file, dst_img_path)
            v3_stats[split]["images"] += 1

            lbl_file = src_lbl_dir / f"{img_file.stem}.txt"
            dst_lbl_path = dst_lbl_dir / f"{new_stem}.txt"

            if not lbl_file.exists():
                dst_lbl_path.touch()
                v3_stats[split]["empty"] += 1
                continue

            with open(lbl_file, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]

            if not lines:
                dst_lbl_path.touch()
                v3_stats[split]["empty"] += 1
                continue

            remapped_lines = []
            for line in lines:
                parts = line.split()
                if not parts:
                    continue
                raw_cls = int(parts[0])
                if raw_cls not in RAW15_TO_CANONICAL:
                    print(f"  [ERROR] Unknown raw class ID {raw_cls} in {lbl_file.name}")
                    continue
                canonical_cls = RAW15_TO_CANONICAL[raw_cls]
                coords = [float(x) for x in parts[1:5]]
                remapped_lines.append(f"{canonical_cls} {coords[0]:.6f} {coords[1]:.6f} {coords[2]:.6f} {coords[3]:.6f}")

            if remapped_lines:
                with open(dst_lbl_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(remapped_lines) + "\n")
                v3_stats[split]["boxes"] += len(remapped_lines)
            else:
                dst_lbl_path.touch()
                v3_stats[split]["empty"] += 1

        print(f"  Processed {split:<5s}: {v3_stats[split]['images']:4d} images | "
              f"{v3_stats[split]['boxes']:4d} boxes | {v3_stats[split]['empty']:3d} clean negatives")

    # ----------------------------------------------------
    # Step 3: Ingest Unique Images from Dataset_pre
    # ----------------------------------------------------
    print("\n[3/5] Cross-Referencing Dataset_pre with Version 3 Dataset...")
    pre_unique_count = 0
    pre_unique_boxes = 0
    pre_duplicate_count = 0

    train_dst_img_dir = dest_path / "train" / "images"
    train_dst_lbl_dir = dest_path / "train" / "labels"

    for pre_split in splits:
        src_img_dir = pre_path / pre_split / "images"
        src_lbl_dir = pre_path / pre_split / "labels"

        if not src_img_dir.exists():
            continue

        for img_file in src_img_dir.glob("*.*"):
            if img_file.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
                continue

            md5_val = compute_md5(img_file)
            if md5_val in v3_hashes:
                pre_duplicate_count += 1
                # Already included with authoritative latest Roboflow v3 annotations
                continue

            # Unique image present ONLY in Dataset_pre -> add to train split
            pre_unique_count += 1
            new_stem = f"pre_{img_file.stem}"
            dst_img_path = train_dst_img_dir / f"{new_stem}{img_file.suffix.lower()}"
            shutil.copy2(img_file, dst_img_path)

            lbl_file = src_lbl_dir / f"{img_file.stem}.txt"
            dst_lbl_path = train_dst_lbl_dir / f"{new_stem}.txt"

            if lbl_file.exists():
                with open(lbl_file, "r", encoding="utf-8") as f:
                    lines = [l.strip() for l in f if l.strip()]
                if lines:
                    shutil.copy2(lbl_file, dst_lbl_path)
                    pre_unique_boxes += len(lines)
                else:
                    dst_lbl_path.touch()
            else:
                dst_lbl_path.touch()

    print(f"  Overlapping Images (Resolved to v3 labels): {pre_duplicate_count}")
    print(f"  Unique Field Images Added from Dataset_pre: {pre_unique_count} images ({pre_unique_boxes} boxes)")

    # ----------------------------------------------------
    # Step 4: Write Consolidated YAML Config
    # ----------------------------------------------------
    print("\n[4/5] Writing Consolidated Dataset Configuration (data.yaml)...")
    yaml_data = {
        "path": str(dest_path).replace("\\", "/"),
        "train": "train/images",
        "val": "valid/images",
        "test": "test/images",
        "nc": len(CANONICAL_NAMES),
        "names": {i: name for i, name in enumerate(CANONICAL_NAMES)}
    }

    yaml_file = dest_path / "data.yaml"
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f, sort_keys=False)

    print(f"  Config successfully saved to: {yaml_file}")

    # ----------------------------------------------------
    # Step 5: Full Dataset Audit & Leakage Check
    # ----------------------------------------------------
    print("\n[5/5] Auditing Consolidated Dataset Integrity & Leakage...")
    grand_class_boxes = Counter()
    grand_class_imgs = defaultdict(set)
    total_imgs = 0
    total_boxes = 0
    total_clean = 0

    split_hashes = defaultdict(set)
    split_summary = {}

    for split in splits:
        img_dir = dest_path / split / "images"
        lbl_dir = dest_path / split / "labels"

        split_boxes = Counter()
        split_imgs = 0
        split_clean = 0

        for img_p in img_dir.glob("*.*"):
            if img_p.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
                continue
            split_imgs += 1
            total_imgs += 1
            h = compute_md5(img_p)
            split_hashes[split].add(h)

            lbl_p = lbl_dir / f"{img_p.stem}.txt"
            if not lbl_p.exists():
                split_clean += 1
                total_clean += 1
                continue

            with open(lbl_p, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]

            if not lines:
                split_clean += 1
                total_clean += 1
                continue

            seen_in_img = set()
            for l in lines:
                parts = l.split()
                cid = int(parts[0])
                split_boxes[cid] += 1
                grand_class_boxes[cid] += 1
                total_boxes += 1
                seen_in_img.add(cid)

            for cid in seen_in_img:
                grand_class_imgs[cid].add(img_p.stem)

        split_summary[split] = {
            "images": split_imgs,
            "boxes": sum(split_boxes.values()),
            "clean": split_clean,
            "class_boxes": dict(sorted(split_boxes.items()))
        }

    # Leakage check
    train_val_leak = split_hashes["train"] & split_hashes["valid"]
    train_test_leak = split_hashes["train"] & split_hashes["test"]
    val_test_leak = split_hashes["valid"] & split_hashes["test"]

    print("\n" + "=" * 70)
    print("CONSOLIDATED DATASET AUDIT REPORT")
    print("=" * 70)
    print(f"Total Consolidated Images:     {total_imgs}")
    print(f"Total Defect Bounding Boxes:   {total_boxes}")
    print(f"Total Background Negatives:    {total_clean} ({total_clean/total_imgs*100:.1f}%)")
    print(f"Train/Val Leakage:             {len(train_val_leak)} images")
    print(f"Train/Test Leakage:            {len(train_test_leak)} images")
    print(f"Val/Test Leakage:              {len(val_test_leak)} images")
    print("-" * 70)
    for s, info in split_summary.items():
        print(f"  Split '{s.upper():5s}': {info['images']:4d} images | {info['boxes']:4d} boxes | {info['clean']:3d} clean negatives")

    print("\n---------------- Per-Class Distribution (All Splits) ----------------")
    print(f"{'ID':<3} {'Class Name':<22} {'Total Boxes':<12} {'Unique Images':<14} {'Train Boxes':<12}")
    print("-" * 65)
    for cid in range(len(CANONICAL_NAMES)):
        cname = CANONICAL_NAMES[cid]
        boxes = grand_class_boxes[cid]
        imgs = len(grand_class_imgs[cid])
        train_boxes = split_summary["train"]["class_boxes"].get(cid, 0)
        print(f"{cid:<3} {cname:<22} {boxes:<12} {imgs:<14} {train_boxes:<12}")
    print("=" * 70)

    assert len(train_val_leak) == 0, "Train-Val data leakage detected!"
    assert len(train_test_leak) == 0, "Train-Test data leakage detected!"
    assert len(val_test_leak) == 0, "Val-Test data leakage detected!"
    print("\n>>> DATA INTEGRITY VERIFIED: ZERO DATA LEAKAGE CONFIRMED <<<\n")

    return split_summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remap and merge Railway_defect_dataset_1200 + Dataset_pre into Dataset_consolidated")
    parser.add_argument("--v3-dir", type=str, default="Railway_defect_dataset_1200", help="Path to v3 dataset")
    parser.add_argument("--pre-dir", type=str, default="Dataset_pre", help="Path to pre dataset")
    parser.add_argument("--dest-dir", type=str, default="Dataset_consolidated", help="Path to destination Dataset_consolidated")
    args = parser.parse_args()

    remap_and_merge(v3_dir=args.v3_dir, pre_dir=args.pre_dir, dest_dir=args.dest_dir)

