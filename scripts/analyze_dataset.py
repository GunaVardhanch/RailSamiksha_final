"""
Comprehensive Railway Track Anomaly Dataset Analysis & Integrity Verification Suite
Audits image resolutions, label validity, class distributions, bounding box geometries,
and SAHI slicing feasibility for RailSamiksha 4K Drone Defect Detection.
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
import yaml
import cv2
import numpy as np
import pandas as pd
from PIL import Image

def load_yaml(yaml_path: Path):
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def analyze_dataset(dataset_root: Path, yaml_path: Path):
    meta = load_yaml(yaml_path)
    class_names = meta.get("names", [])
    if isinstance(class_names, dict):
        class_names = [class_names[i] for i in sorted(class_names.keys())]
    num_classes = len(class_names)
    print("=" * 80)
    print(f"RAILSAMIKSHA DATASET AUDIT & ANALYSIS")
    print(f"Root: {dataset_root.resolve()}")
    print(f"Classes ({num_classes}): {class_names}")
    print("=" * 80)

    splits = ["train", "valid", "test"]
    stats = {
        "split_counts": {},
        "corrupted_images": [],
        "missing_labels": [],
        "empty_labels": [],
        "invalid_boxes": [],
        "class_counts_by_split": {s: defaultdict(int) for s in splits},
        "total_boxes_by_split": defaultdict(int),
        "resolutions": defaultdict(int),
        "box_metrics": [],
    }

    for split in splits:
        split_dir = dataset_root / split
        img_dir = split_dir / "images"
        lbl_dir = split_dir / "labels"

        if not img_dir.exists():
            print(f"[WARN] Images directory missing for split: {split}")
            continue

        img_files = sorted([f for f in img_dir.iterdir() if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]])
        lbl_files = sorted([f for f in lbl_dir.iterdir() if f.is_file() and f.suffix.lower() == ".txt"]) if lbl_dir.exists() else []

        lbl_map = {f.stem: f for f in lbl_files}
        stats["split_counts"][split] = {
            "images": len(img_files),
            "labels": len(lbl_files),
            "with_annotations": 0,
            "zero_annotations": 0,
        }

        print(f"\nAnalyzing split '{split}': {len(img_files)} images, {len(lbl_files)} label files...")

        for img_path in img_files:
            # Check image integrity & resolution
            try:
                with Image.open(img_path) as img:
                    w, h = img.size
                    mode = img.mode
                    stats["resolutions"][(w, h, mode)] += 1
            except Exception as e:
                stats["corrupted_images"].append((str(img_path), str(e)))
                continue

            lbl_path = lbl_map.get(img_path.stem)
            if not lbl_path or not lbl_path.exists():
                stats["missing_labels"].append(str(img_path))
                stats["split_counts"][split]["zero_annotations"] += 1
                continue

            with open(lbl_path, "r", encoding="utf-8") as lf:
                lines = [l.strip() for l in lf.readlines() if l.strip()]

            if not lines:
                stats["empty_labels"].append(str(lbl_path))
                stats["split_counts"][split]["zero_annotations"] += 1
                continue

            stats["split_counts"][split]["with_annotations"] += 1

            for line_idx, line in enumerate(lines, 1):
                parts = line.split()
                if len(parts) < 5:
                    stats["invalid_boxes"].append((str(lbl_path), line_idx, f"Malformed line (< 5 parts): {line}"))
                    continue

                try:
                    cls_id = int(parts[0])
                    xc, yc, bw, bh = map(float, parts[1:5])
                except ValueError:
                    stats["invalid_boxes"].append((str(lbl_path), line_idx, f"Non-numeric values: {line}"))
                    continue

                # Coordinate validation
                if cls_id < 0 or cls_id >= num_classes:
                    stats["invalid_boxes"].append((str(lbl_path), line_idx, f"Class ID {cls_id} out of bounds [0, {num_classes-1}]"))

                if not (0.0 <= xc <= 1.0 and 0.0 <= yc <= 1.0 and 0.0 < bw <= 1.0 and 0.0 < bh <= 1.0):
                    stats["invalid_boxes"].append((str(lbl_path), line_idx, f"Coords out of bounds: xc={xc}, yc={yc}, w={bw}, h={bh}"))

                # Convert to absolute pixel dimensions
                abs_w = bw * w
                abs_h = bh * h
                abs_area = abs_w * abs_h
                rel_area = bw * bh

                stats["class_counts_by_split"][split][cls_id] += 1
                stats["total_boxes_by_split"][split] += 1

                stats["box_metrics"].append({
                    "split": split,
                    "image": img_path.name,
                    "img_w": w,
                    "img_h": h,
                    "class_id": cls_id,
                    "class_name": class_names[cls_id] if 0 <= cls_id < num_classes else f"Unknown({cls_id})",
                    "xc": xc,
                    "yc": yc,
                    "bw": bw,
                    "bh": bh,
                    "abs_w": abs_w,
                    "abs_h": abs_h,
                    "abs_area": abs_area,
                    "rel_area_pct": rel_area * 100.0,
                    "aspect_ratio": abs_w / (abs_h + 1e-6),
                })

    return stats, class_names

def generate_report(stats, class_names, output_dir: Path, dataset_root: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    df_boxes = pd.DataFrame(stats["box_metrics"])

    print("\n" + "=" * 80)
    print("DATASET INTEGRITY & VALIDATION SUMMARY")
    print("=" * 80)

    # 1. Split summary table
    print("\n[1] SPLIT DISTRIBUTION:")
    split_summary = []
    for split, counts in stats["split_counts"].items():
        box_count = stats["total_boxes_by_split"].get(split, 0)
        split_summary.append({
            "Split": split,
            "Images": counts["images"],
            "Annotated Images": counts["with_annotations"],
            "Empty Images": counts["zero_annotations"],
            "Total BBoxes": box_count,
            "Avg Boxes/Img": round(box_count / max(counts["with_annotations"], 1), 2)
        })
    df_splits = pd.DataFrame(split_summary)
    print(df_splits.to_string(index=False))

    # 2. Image Resolutions
    print("\n[2] IMAGE RESOLUTIONS & CHANNELS:")
    res_list = [{"Width": k[0], "Height": k[1], "Color Mode": k[2], "Count": v} for k, v in stats["resolutions"].items()]
    df_res = pd.DataFrame(res_list)
    print(df_res.to_string(index=False))

    # 3. Class distribution across splits
    print("\n[3] CLASS FREQUENCY DISTRIBUTION:")
    class_rows = []
    for idx, cname in enumerate(class_names):
        train_c = stats["class_counts_by_split"]["train"][idx]
        val_c = stats["class_counts_by_split"]["valid"][idx]
        test_c = stats["class_counts_by_split"]["test"][idx]
        tot = train_c + val_c + test_c
        class_rows.append({
            "ID": idx,
            "Class Name": cname,
            "Train": train_c,
            "Valid": val_c,
            "Test": test_c,
            "Total": tot,
            "Share (%)": 0.0
        })
    df_classes = pd.DataFrame(class_rows)
    total_all_boxes = df_classes["Total"].sum()
    if total_all_boxes > 0:
        df_classes["Share (%)"] = ((df_classes["Total"] / total_all_boxes) * 100).round(2)
    print(df_classes.to_string(index=False))

    # 4. Box Geometries & Object Size Distribution (COCO criteria)
    # COCO criteria: Small (< 32^2 = 1024 px^2), Medium (1024 - 9216 px^2), Large (> 9216 px^2)
    print("\n[4] BOUNDING BOX SCALE & GEOMETRY (COCO Standard):")
    if not df_boxes.empty:
        small_mask = df_boxes["abs_area"] < 1024
        medium_mask = (df_boxes["abs_area"] >= 1024) & (df_boxes["abs_area"] <= 9216)
        large_mask = df_boxes["abs_area"] > 9216

        n_total = len(df_boxes)
        n_small = small_mask.sum()
        n_med = medium_mask.sum()
        n_large = large_mask.sum()

        scale_df = pd.DataFrame([
            {"Category": "Small (< 32x32 px / < 1024 px²)", "Count": n_small, "Percentage (%)": round(100 * n_small / n_total, 2)},
            {"Category": "Medium (32x32 to 96x96 px / 1024-9216 px²)", "Count": n_med, "Percentage (%)": round(100 * n_med / n_total, 2)},
            {"Category": "Large (> 96x96 px / > 9216 px²)", "Count": n_large, "Percentage (%)": round(100 * n_large / n_total, 2)},
        ])
        print(scale_df.to_string(index=False))

        print("\n[5] PER-CLASS BOUNDING BOX DIMENSIONS (PIXELS):")
        box_stats = df_boxes.groupby("class_name").agg(
            Count=("abs_area", "count"),
            Mean_W=("abs_w", "mean"),
            Mean_H=("abs_h", "mean"),
            Min_W=("abs_w", "min"),
            Min_H=("abs_h", "min"),
            Max_W=("abs_w", "max"),
            Max_H=("abs_h", "max"),
            Median_Area=("abs_area", "median"),
            Mean_AspectRatio=("aspect_ratio", "mean")
        ).round(1).reset_index()
        print(box_stats.to_string(index=False))
    else:
        print("No bounding boxes found!")

    # 6. Integrity issues
    print("\n[6] INTEGRITY & ERROR LOG:")
    print(f"- Corrupted Images: {len(stats['corrupted_images'])}")
    print(f"- Missing Label Files: {len(stats['missing_labels'])}")
    print(f"- Empty Label Files: {len(stats['empty_labels'])}")
    print(f"- Invalid Bounding Boxes: {len(stats['invalid_boxes'])}")

    if stats["invalid_boxes"]:
        print("\nSample Invalid Boxes (First 5):")
        for inv in stats["invalid_boxes"][:5]:
            print(f"  {inv}")

    # Export CSVs & Markdown report
    report_md_path = output_dir / "DATASET_AUDIT_REPORT.md"
    csv_classes_path = output_dir / "class_distribution.csv"
    csv_boxes_path = output_dir / "bounding_box_metrics.csv"

    df_classes.to_csv(csv_classes_path, index=False)
    if not df_boxes.empty:
        df_boxes.to_csv(csv_boxes_path, index=False)

    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write("# RailSamiksha Dataset Audit & Exploratory Data Analysis\n\n")
        f.write(f"- **Dataset Path:** `{dataset_root.resolve()}`\n")
        f.write(f"- **Classes Count:** {len(class_names)}\n\n")
        f.write("## 1. Split Distribution\n\n")
        f.write(df_splits.to_markdown(index=False) + "\n\n")
        f.write("## 2. Image Resolutions\n\n")
        f.write(df_res.to_markdown(index=False) + "\n\n")
        f.write("## 3. Class Distribution Across Splits\n\n")
        f.write(df_classes.to_markdown(index=False) + "\n\n")
        if not df_boxes.empty:
            f.write("## 4. Object Scale Categories (COCO Criteria)\n\n")
            f.write(scale_df.to_markdown(index=False) + "\n\n")
            f.write("## 5. Bounding Box Geometry per Class\n\n")
            f.write(box_stats.to_markdown(index=False) + "\n\n")
        f.write("## 6. Dataset Quality & Integrity Check\n\n")
        f.write(f"- Corrupted images: `{len(stats['corrupted_images'])}`\n")
        f.write(f"- Missing label files: `{len(stats['missing_labels'])}`\n")
        f.write(f"- Empty label files (background images): `{len(stats['empty_labels'])}`\n")
        f.write(f"- Invalid bounding boxes: `{len(stats['invalid_boxes'])}`\n")

    print(f"\nAudit complete! Reports saved to:\n  - {report_md_path}\n  - {csv_classes_path}\n  - {csv_boxes_path}")

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    dataset_dir = project_root / "Dataset_pre"
    yaml_file = dataset_dir / "data.yaml"
    reports_dir = project_root / "reports"

    if not dataset_dir.exists() or not yaml_file.exists():
        print(f"Error: Dataset or data.yaml not found at {dataset_dir}")
        sys.exit(1)

    stats, class_names = analyze_dataset(dataset_dir, yaml_file)
    generate_report(stats, class_names, reports_dir, dataset_dir)
