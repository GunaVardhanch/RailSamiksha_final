"""
RailSamiksha 1:1 Scale SAHI Slicer & Label Sanitizer (tools/slice_dataset_v3.py)
================================================================================
Implements Production Scale-Preserving Tiling:
  - Eliminates 4K/2.7K-to-640 resolution downscaling collapse for tiny defects.
  - Slices high-resolution drone frames into native 640x640 patches with 20% overlap.
  - Sanitizes Sleeper Defect macro-boxes (clamps full-tie rectangles to damaged zones).
  - Regularizes Pandrol fastener bounding box footprints.
  - Retains 15% hard background negatives for false-positive suppression.
  - Strictly preserves train/valid/test split isolation (zero cross-leakage).
"""

import os
import cv2
import random
import shutil
import hashlib
from pathlib import Path
from collections import Counter, defaultdict
import yaml
import numpy as np

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

def calculate_slice_positions(dim: int, tile_size: int, stride: int):
    coords = list(range(0, max(1, dim - tile_size + 1), stride))
    if not coords or (coords[-1] + tile_size < dim):
        coords.append(max(0, dim - tile_size))
    return sorted(list(set(coords)))

def sanitize_box(cid: int, xc: float, yc: float, bw: float, bh: float):
    """
    Sanitizes outlier annotations:
    - Sleeper Defect (8): clamps full-tie vertical rectangles (h > 0.40, w < 0.10) to h <= 0.35.
    - Fasteners (1, 3): bounds Pandrol clip scales to realistic dimensions.
    """
    if cid == 8:
        # Full-tie vertical sleeper
        if bh > 0.40 and bw < 0.10:
            bh = min(0.35, bh)
        elif bw > 0.40 and bh < 0.10:
            bw = min(0.35, bw)
    elif cid in (1, 3):
        # Fasteners
        bw = max(0.015, min(0.12, bw))
        bh = max(0.015, min(0.12, bh))

    return cid, xc, yc, bw, bh

def slice_and_sanitize_dataset(
    source_dir: str = "Dataset_consolidated",
    output_dir: str = "Dataset_tiled_v3",
    tile_size: int = 640,
    overlap: float = 0.20,
    min_box_area_ratio: float = 0.30,
    keep_empty_ratio: float = 0.15,
    seed: int = 42
):
    random.seed(seed)
    np.random.seed(seed)

    stride = int(tile_size * (1.0 - overlap))
    splits = ["train", "valid", "test"]
    src_path = Path(source_dir).resolve()
    dst_path = Path(output_dir).resolve()

    print("=" * 75)
    print("RAILSAMIKSHA NATIVE 1:1 SCALE SAHI SLICER & LABEL SANITIZER")
    print(f"Source Directory:     {src_path}")
    print(f"Destination Output:   {dst_path}")
    print(f"Tile Size:            {tile_size}x{tile_size} (1:1 pixel scale)")
    print(f"Stride / Overlap:     {stride}px step ({int(overlap*100)}% overlap)")
    print(f"Negative Bank Ratio:  {int(keep_empty_ratio*100)}%")
    print("=" * 75)

    if dst_path.exists():
        print(f"\n[1/4] Cleaning existing output directory {dst_path}...")
        shutil.rmtree(dst_path)

    dst_path.mkdir(parents=True, exist_ok=True)

    split_stats = {}

    for split in splits:
        print(f"\n[2/4] Slicing & Sanitizing '{split.upper()}' Split...")
        src_img_dir = src_path / split / "images"
        src_lbl_dir = src_path / split / "labels"
        dst_img_dir = dst_path / split / "images"
        dst_lbl_dir = dst_path / split / "labels"

        dst_img_dir.mkdir(parents=True, exist_ok=True)
        dst_lbl_dir.mkdir(parents=True, exist_ok=True)

        img_paths = sorted([p for p in src_img_dir.glob("*.*") if p.suffix.lower() in [".jpg", ".jpeg", ".png"]])
        
        defect_tiles = 0
        empty_tiles = 0
        preserved_direct = 0
        class_counter = Counter()

        for img_idx, img_p in enumerate(img_paths):
            img = cv2.imread(str(img_p))
            if img is None:
                continue
            h, w = img.shape[:2]
            stem = img_p.stem

            # Load and sanitize annotations
            lbl_p = src_lbl_dir / f"{stem}.txt"
            boxes = []
            if lbl_p.exists():
                with open(lbl_p, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            cid = int(parts[0])
                            xc, yc, bw, bh = map(float, parts[1:5])
                            cid, xc, yc, bw, bh = sanitize_box(cid, xc, yc, bw, bh)
                            bx1 = (xc - bw / 2.0) * w
                            by1 = (yc - bh / 2.0) * h
                            bx2 = (xc + bw / 2.0) * w
                            by2 = (yc + bh / 2.0) * h
                            orig_area = max(1e-6, (bx2 - bx1) * (by2 - by1))
                            boxes.append((cid, bx1, by1, bx2, by2, orig_area))

            # If image is already native patch size (e.g. 512x512 or 640x640), preserve directly
            if w <= tile_size and h <= tile_size:
                out_img_p = dst_img_dir / f"{stem}.jpg"
                cv2.imwrite(str(out_img_p), img)
                out_lbl_p = dst_lbl_dir / f"{stem}.txt"
                with open(out_lbl_p, "w", encoding="utf-8") as f:
                    for cid, bx1, by1, bx2, by2, _ in boxes:
                        xc = ((bx1 + bx2) / 2.0) / w
                        yc = ((by1 + by2) / 2.0) / h
                        bw = (bx2 - bx1) / w
                        bh = (by2 - by1) / h
                        f.write(f"{cid} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n")
                        class_counter[cid] += 1
                preserved_direct += 1
                if boxes:
                    defect_tiles += 1
                else:
                    empty_tiles += 1
                continue

            # Multi-tile 1:1 scale sliding grid
            xs = calculate_slice_positions(w, tile_size, stride)
            ys = calculate_slice_positions(h, tile_size, stride)

            img_defect_tiles = []
            img_empty_tiles = []
            patch_idx = 0

            for y1 in ys:
                for x1 in xs:
                    x2 = min(w, x1 + tile_size)
                    y2 = min(h, y1 + tile_size)
                    act_x1 = max(0, x2 - tile_size)
                    act_y1 = max(0, y2 - tile_size)

                    crop = img[act_y1:y2, act_x1:x2]
                    if crop.shape[0] != tile_size or crop.shape[1] != tile_size:
                        crop = cv2.resize(crop, (tile_size, tile_size), interpolation=cv2.INTER_LINEAR)

                    tile_boxes = []
                    for cid, bx1, by1, bx2, by2, orig_area in boxes:
                        ix1 = max(float(act_x1), bx1)
                        iy1 = max(float(act_y1), by1)
                        ix2 = min(float(x2), bx2)
                        iy2 = min(float(y2), by2)

                        if ix2 > ix1 and iy2 > iy1:
                            inter_area = (ix2 - ix1) * (iy2 - iy1)
                            if (inter_area / orig_area) >= min_box_area_ratio:
                                n_xc = ((ix1 + ix2) / 2.0 - act_x1) / tile_size
                                n_yc = ((iy1 + iy2) / 2.0 - act_y1) / tile_size
                                n_bw = (ix2 - ix1) / tile_size
                                n_bh = (iy2 - iy1) / tile_size

                                n_xc = max(0.0, min(1.0, n_xc))
                                n_yc = max(0.0, min(1.0, n_yc))
                                n_bw = max(0.0, min(1.0, n_bw))
                                n_bh = max(0.0, min(1.0, n_bh))

                                tile_boxes.append((cid, n_xc, n_yc, n_bw, n_bh))

                    patch_name = f"{stem}_p{patch_idx:03d}"
                    if tile_boxes:
                        img_defect_tiles.append((patch_name, crop, tile_boxes))
                    else:
                        img_empty_tiles.append((patch_name, crop, []))
                    patch_idx += 1

            # Save all defect-positive tiles
            for pname, pcrop, pboxes in img_defect_tiles:
                cv2.imwrite(str(dst_img_dir / f"{pname}.jpg"), pcrop)
                with open(dst_lbl_dir / f"{pname}.txt", "w", encoding="utf-8") as f:
                    for b in pboxes:
                        f.write(f"{b[0]} {b[1]:.6f} {b[2]:.6f} {b[3]:.6f} {b[4]:.6f}\n")
                        class_counter[b[0]] += 1
                defect_tiles += 1

            # Sample hard negative empty tiles up to keep_empty_ratio
            num_empty_to_keep = max(1 if img_defect_tiles else 0, int(len(img_defect_tiles) * keep_empty_ratio))
            if img_empty_tiles and num_empty_to_keep > 0:
                selected_empty = random.sample(img_empty_tiles, min(num_empty_to_keep, len(img_empty_tiles)))
                for pname, pcrop, _ in selected_empty:
                    cv2.imwrite(str(dst_img_dir / f"{pname}.jpg"), pcrop)
                    (dst_lbl_dir / f"{pname}.txt").touch()
                    empty_tiles += 1

        print(f"  Result '{split}': {defect_tiles} defect tiles, {empty_tiles} clean negatives (Total: {defect_tiles + empty_tiles})")
        split_stats[split] = {
            "defect_tiles": defect_tiles,
            "empty_tiles": empty_tiles,
            "total_tiles": defect_tiles + empty_tiles,
            "classes": dict(sorted(class_counter.items()))
        }

    # ----------------------------------------------------
    # Step 3: Write Dataset YAML
    # ----------------------------------------------------
    print("\n[3/4] Writing YAML Configuration (Dataset_tiled_v3/data.yaml)...")
    yaml_data = {
        "path": str(dst_path).replace("\\", "/"),
        "train": "train/images",
        "val": "valid/images",
        "test": "test/images",
        "nc": len(CANONICAL_NAMES),
        "names": {i: name for i, name in enumerate(CANONICAL_NAMES)}
    }
    yaml_file = dst_path / "data.yaml"
    with open(yaml_file, "w", encoding="utf-8") as f:
        yaml.dump(yaml_data, f, sort_keys=False)

    print(f"Saved: {yaml_file}")

    # ----------------------------------------------------
    # Step 4: Verification & Split Leakage Check
    # ----------------------------------------------------
    print("\n[4/4] Verifying Dataset Integrity & Zero Leakage...")
    split_hashes = defaultdict(set)
    for s in splits:
        for p in (dst_path / s / "images").glob("*.*"):
            split_hashes[s].add(hashlib.md5(p.read_bytes()).hexdigest())

    leak_tv = split_hashes["train"] & split_hashes["valid"]
    leak_tt = split_hashes["train"] & split_hashes["test"]
    leak_vt = split_hashes["valid"] & split_hashes["test"]

    print("\n" + "=" * 75)
    print("TILED DATASET SUMMARY & AUDIT REPORT")
    print("=" * 75)
    total_imgs = sum(s["total_tiles"] for s in split_stats.values())
    total_boxes = sum(sum(s["classes"].values()) for s in split_stats.values())
    total_clean = sum(s["empty_tiles"] for s in split_stats.values())
    print(f"Total 1:1 Scale Patches:        {total_imgs}")
    print(f"Total Defect Bounding Boxes:    {total_boxes}")
    print(f"Total Clean Background Tiles:   {total_clean} ({total_clean/total_imgs*100:.1f}%)")
    print(f"Train/Val Leakage:              {len(leak_tv)} tiles")
    print(f"Train/Test Leakage:             {len(leak_tt)} tiles")
    print(f"Val/Test Leakage:               {len(leak_vt)} tiles")
    print("-" * 75)
    for s, info in split_stats.items():
        print(f"  Split '{s.upper():5s}': {info['total_tiles']:4d} patches | {sum(info['classes'].values()):4d} boxes | {info['empty_tiles']:3d} negatives")

    print("\n---------------- Per-Class Distribution in Train Split ----------------")
    print(f"{'ID':<3} {'Class Name':<22} {'Train Boxes':<12}")
    print("-" * 45)
    for cid in range(len(CANONICAL_NAMES)):
        cname = CANONICAL_NAMES[cid]
        boxes = split_stats["train"]["classes"].get(cid, 0)
        print(f"{cid:<3} {cname:<22} {boxes:<12}")
    print("=" * 75)

    assert len(leak_tv) == 0, "Train/Val leakage detected!"
    assert len(leak_tt) == 0, "Train/Test leakage detected!"
    assert len(leak_vt) == 0, "Val/Test leakage detected!"
    print("\n>>> DATA INTEGRITY VERIFIED: ZERO DATA LEAKAGE CONFIRMED <<<\n")

if __name__ == "__main__":
    slice_and_sanitize_dataset()

