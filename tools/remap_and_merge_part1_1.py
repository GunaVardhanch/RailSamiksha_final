"""
Remap & Merge Part 1.1 into Consolidated Dataset (tools/remap_and_merge_part1_1.py)
==================================================================================
Merges:
  1. Dataset_tiled (canonical 9 classes, 640x640 patches)
  2. Dats set final version part 1.1 (raw 11 classes, 512x512 images)
into:
  Dataset_consolidated (strictly standardized 9-class dataset ready for RT-DETR-L training)

Class Mapping:
  Raw 0, 1 ('Ballast Deficiency')        -> Canonical 0 (Ballast Defect)
  Raw 4    ('Damaged Fastener')           -> Canonical 1 (Damaged Fastener)
  Raw 5    ('Foreign Objects')            -> Canonical 2 (Foreign Objects)
  Raw 6    ('Missing Fastener')           -> Canonical 3 (Missing Fastener)
  Raw 7    ('Rail Crack')                 -> Canonical 4 (Rail Crack)
  Raw 8    ('Rail Joint Damage')          -> Canonical 5 (Rail Joint Damage)
  Raw 9    ('Rail Misalignment')          -> Canonical 6 (Rail Misalignment)
  Raw 10   ('Rail Wear')                  -> Canonical 7 (Rail Wear)
  Raw 2, 3 ('Broken / Missing Sleeper')   -> Canonical 8 (Sleeper Defect)
"""

import os
import shutil
import argparse
from pathlib import Path
from collections import Counter, defaultdict
import yaml

RAW_TO_CANONICAL = {
    0: 0,   # Ballast  Deficiency -> Ballast Defect
    1: 0,   # Ballast Deficiency -> Ballast Defect
    4: 1,   # Damaged Fastener -> Damaged Fastener
    5: 2,   # Foreign Objects -> Foreign Objects
    6: 3,   # Missing Fastener -> Missing Fastener
    7: 4,   # Rail Crack -> Rail Crack
    8: 5,   # Rail Joint Damage -> Rail Joint Damage
    9: 6,   # Rail Misalignment -> Rail Misalignment
    10: 7,  # Rail Wear -> Rail Wear
    2: 8,   # Broken - Missing Sleeper -> Sleeper Defect
    3: 8,   # Broken Sleeper -> Sleeper Defect
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

def remap_and_merge(
    tiled_dir: str = "Dataset_tiled",
    part1_dir: str = "Dats set final version part 1.1",
    dest_dir: str = "Dataset_consolidated"
):
    tiled_path = Path(tiled_dir).resolve()
    part1_path = Path(part1_dir).resolve()
    dest_path = Path(dest_dir).resolve()

    print(f"==================================================")
    print(f"CANONICAL DATASET CONSOLIDATION")
    print(f"Source 1 (Tiled Dataset):   {tiled_path}")
    print(f"Source 2 (Part 1.1 Scaled): {part1_path}")
    print(f"Target Output Directory:    {dest_path}")
    print(f"==================================================\n")

    splits = ["train", "valid", "test"]

    # Recreate destination directories
    if dest_path.exists():
        print(f"Target directory {dest_path} already exists. Cleaning up...")
        shutil.rmtree(dest_path)

    for split in splits:
        (dest_path / split / "images").mkdir(parents=True, exist_ok=True)
        (dest_path / split / "labels").mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------
    # Step 1: Copy Dataset_tiled (Source 1)
    # ----------------------------------------------------
    print("--- [1/3] Ingesting Dataset_tiled (Source 1) ---")
    tiled_stats = {s: {"images": 0, "boxes": 0, "empty": 0} for s in splits}

    for split in splits:
        src_img_dir = tiled_path / split / "images"
        src_lbl_dir = tiled_path / split / "labels"
        dst_img_dir = dest_path / split / "images"
        dst_lbl_dir = dest_path / split / "labels"

        if not src_img_dir.exists():
            print(f"  [Warning] Missing {src_img_dir}")
            continue

        for img_file in src_img_dir.glob("*.*"):
            new_stem = f"tiled_{img_file.stem}"
            dst_img_path = dst_img_dir / f"{new_stem}{img_file.suffix.lower()}"
            shutil.copy2(img_file, dst_img_path)
            tiled_stats[split]["images"] += 1

            lbl_file = src_lbl_dir / f"{img_file.stem}.txt"
            dst_lbl_path = dst_lbl_dir / f"{new_stem}.txt"

            if lbl_file.exists():
                with open(lbl_file, "r", encoding="utf-8") as f:
                    lines = [l.strip() for l in f if l.strip()]
                if lines:
                    shutil.copy2(lbl_file, dst_lbl_path)
                    tiled_stats[split]["boxes"] += len(lines)
                else:
                    dst_lbl_path.touch()
                    tiled_stats[split]["empty"] += 1
            else:
                dst_lbl_path.touch()
                tiled_stats[split]["empty"] += 1

        print(f"  Copied {split}: {tiled_stats[split]['images']} images, "
              f"{tiled_stats[split]['boxes']} boxes, {tiled_stats[split]['empty']} clean backgrounds")

    # ----------------------------------------------------
    # Step 2: Remap & Merge Part 1.1 (Source 2)
    # ----------------------------------------------------
    print("\n--- [2/3] Remapping & Merging Part 1.1 (Source 2) ---")
    part1_stats = {s: {"images": 0, "boxes": 0, "empty": 0} for s in splits}

    for split in splits:
        src_img_dir = part1_path / split / "images"
        src_lbl_dir = part1_path / split / "labels"
        dst_img_dir = dest_path / split / "images"
        dst_lbl_dir = dest_path / split / "labels"

        if not src_img_dir.exists():
            print(f"  [Warning] Missing {src_img_dir}")
            continue

        for img_file in src_img_dir.glob("*.*"):
            new_stem = f"p11_{img_file.stem}"
            dst_img_path = dst_img_dir / f"{new_stem}{img_file.suffix.lower()}"
            shutil.copy2(img_file, dst_img_path)
            part1_stats[split]["images"] += 1

            lbl_file = src_lbl_dir / f"{img_file.stem}.txt"
            dst_lbl_path = dst_lbl_dir / f"{new_stem}.txt"

            if not lbl_file.exists():
                dst_lbl_path.touch()
                part1_stats[split]["empty"] += 1
                continue

            with open(lbl_file, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]

            if not lines:
                dst_lbl_path.touch()
                part1_stats[split]["empty"] += 1
                continue

            remapped_lines = []
            for line in lines:
                parts = line.split()
                if not parts:
                    continue
                raw_cls = int(parts[0])
                if raw_cls not in RAW_TO_CANONICAL:
                    print(f"  [ERROR] Unknown raw class ID {raw_cls} in {lbl_file.name}")
                    continue
                canonical_cls = RAW_TO_CANONICAL[raw_cls]
                coords = [float(x) for x in parts[1:5]]
                remapped_lines.append(f"{canonical_cls} {coords[0]:.6f} {coords[1]:.6f} {coords[2]:.6f} {coords[3]:.6f}")

            if remapped_lines:
                with open(dst_lbl_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(remapped_lines) + "\n")
                part1_stats[split]["boxes"] += len(remapped_lines)
            else:
                dst_lbl_path.touch()
                part1_stats[split]["empty"] += 1

        print(f"  Remapped & copied {split}: {part1_stats[split]['images']} images, "
              f"{part1_stats[split]['boxes']} boxes, {part1_stats[split]['empty']} clean backgrounds")

    # ----------------------------------------------------
    # Step 3: Write Consolidated YAML Config
    # ----------------------------------------------------
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

    print(f"\nSaved consolidated dataset config: {yaml_file}")

    # ----------------------------------------------------
    # Step 4: Full Dataset Audit & Verification
    # ----------------------------------------------------
    print("\n--- [3/3] Auditing Consolidated Dataset ---")
    grand_class_boxes = Counter()
    grand_class_imgs = defaultdict(set)
    total_imgs = 0
    total_boxes = 0
    total_clean = 0

    split_summary = {}

    for split in splits:
        img_dir = dest_path / split / "images"
        lbl_dir = dest_path / split / "labels"

        split_boxes = Counter()
        split_imgs = 0
        split_clean = 0

        for img_p in img_dir.glob("*.*"):
            split_imgs += 1
            total_imgs += 1
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

    print("\n================ CONSOLIDATED DATASET SUMMARY ================")
    print(f"Total Consolidated Images:          {total_imgs}")
    print(f"Total Defect Bounding Boxes:        {total_boxes}")
    print(f"Total Clean / Negative Images:      {total_clean} ({total_clean/total_imgs*100:.1f}%)")
    print(f"==============================================================")
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
    print("=" * 65)

    return split_summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remap and merge Part 1.1 into canonical Dataset_consolidated")
    parser.add_argument("--tiled-dir", type=str, default="Dataset_tiled", help="Path to Dataset_tiled")
    parser.add_argument("--part1-dir", type=str, default="Dats set final version part 1.1", help="Path to Part 1.1")
    parser.add_argument("--dest-dir", type=str, default="Dataset_consolidated", help="Path to output Dataset_consolidated")
    args = parser.parse_args()

    remap_and_merge(tiled_dir=args.tiled_dir, part1_dir=args.part1_dir, dest_dir=args.dest_dir)
