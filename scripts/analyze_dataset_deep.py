"""
Comprehensive Dataset & Bounding Box Analytical Audit (scripts/analyze_dataset_deep.py)
========================================================================================
Deeply profiles Dataset_consolidated:
  1. Image and Box counts per class per split.
  2. Bounding box pixel scale distributions (width, height, area, aspect ratio).
  3. Micro/Small/Medium/Large scale breakdown.
  4. Label density (boxes per image, multi-label co-occurrence).
  5. Annotation anomalies and noise analysis.
"""

from pathlib import Path
from collections import Counter, defaultdict
import numpy as np

def run_analysis():
    root = Path("Dataset_consolidated")
    classes = [
        "Ballast Defect", "Damaged Fastener", "Foreign Objects",
        "Missing Fastener", "Rail Crack", "Rail Joint Damage",
        "Rail Misalignment", "Rail Wear", "Sleeper Defect"
    ]
    splits = ["train", "valid", "test"]

    stats = {
        c: {
            "boxes": Counter(),
            "imgs": defaultdict(set),
            "widths": [],
            "heights": [],
            "areas_640": [],
            "aspect_ratios": []
        }
        for c in range(9)
    }

    split_totals = {s: {"imgs": 0, "empty": 0, "boxes": 0} for s in splits}
    boxes_per_img = defaultdict(int)
    img_class_sets = defaultdict(set)
    extreme_aspect_boxes = []
    tiny_boxes_count = 0

    for split in splits:
        img_dir = root / split / "images"
        lbl_dir = root / split / "labels"

        for img_p in img_dir.glob("*.*"):
            split_totals[split]["imgs"] += 1
            lbl_p = lbl_dir / f"{img_p.stem}.txt"

            if not lbl_p.exists():
                split_totals[split]["empty"] += 1
                continue

            with open(lbl_p, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]

            if not lines:
                split_totals[split]["empty"] += 1
                continue

            split_totals[split]["boxes"] += len(lines)
            boxes_per_img[img_p.name] = len(lines)

            for l in lines:
                parts = l.split()
                if not parts:
                    continue
                cid = int(parts[0])
                xc, yc, w, h = map(float, parts[1:5])

                stats[cid]["boxes"][split] += 1
                stats[cid]["imgs"][split].add(img_p.name)
                img_class_sets[img_p.name].add(cid)

                w_px = w * 640
                h_px = h * 640
                area_px = w_px * h_px
                ar = w / (h + 1e-6)

                stats[cid]["widths"].append(w_px)
                stats[cid]["heights"].append(h_px)
                stats[cid]["areas_640"].append(area_px)
                stats[cid]["aspect_ratios"].append(ar)

                if area_px < 256:  # Less than 16x16 px
                    tiny_boxes_count += 1
                if ar > 10 or ar < 0.1:
                    extreme_aspect_boxes.append((img_p.name, cid, w_px, h_px, ar))

    print("================================================================================")
    print("                    DATASET CONSOLIDATED: DEEP AUDIT REPORT                     ")
    print("================================================================================")
    total_imgs = sum(t["imgs"] for t in split_totals.values())
    total_boxes = sum(t["boxes"] for t in split_totals.values())
    total_empty = sum(t["empty"] for t in split_totals.values())

    print(f"Total Images: {total_imgs} | Defect Boxes: {total_boxes} | Background (Hard Negatives): {total_empty} ({total_empty/total_imgs*100:.1f}%)")
    print("\n--- Split Distributions ---")
    for s in splits:
        t = split_totals[s]
        def_imgs = t["imgs"] - t["empty"]
        print(f"  {s.upper():<6}: {t['imgs']:4d} images ({def_imgs:4d} defect, {t['empty']:3d} background) | {t['boxes']:4d} boxes | {t['boxes']/max(1, def_imgs):.2f} boxes/defect image")

    print("\n--- Class Instance Distribution Across Splits ---")
    print(f"{'ID':<3} {'Class Name':<20} {'Train':<7} {'Val':<6} {'Test':<6} {'Total Boxes':<12} {'Train Imgs':<11} {'Test Imgs':<10}")
    print("-" * 80)
    for cid in range(9):
        cname = classes[cid]
        b = stats[cid]["boxes"]
        tot_b = sum(b.values())
        train_i = len(stats[cid]["imgs"]["train"])
        test_i = len(stats[cid]["imgs"]["test"])
        print(f"{cid:<3} {cname:<20} {b['train']:<7} {b['valid']:<6} {b['test']:<6} {tot_b:<12} {train_i:<11} {test_i:<10}")

    print("\n--- Bounding Box Scale & Geometry Metrics (at 640x640 resolution) ---")
    print(f"{'ID':<3} {'Class Name':<20} {'Mean WxH':<14} {'Median Area':<13} {'Micro (<32px)':<14} {'Small (32-96)':<14} {'Large (>96px)':<12}")
    print("-" * 88)
    for cid in range(9):
        cname = classes[cid]
        w_arr = np.array(stats[cid]["widths"])
        h_arr = np.array(stats[cid]["heights"])
        a_arr = np.array(stats[cid]["areas_640"])

        avg_w = np.mean(w_arr) if len(w_arr) else 0
        avg_h = np.mean(h_arr) if len(h_arr) else 0
        med_area = np.median(a_arr) if len(a_arr) else 0

        # Scale breakdown: micro (sqrt(area) < 32px), small (32-96px), large (>96px)
        micro_pct = (np.sum(a_arr < 1024) / len(a_arr) * 100) if len(a_arr) else 0
        small_pct = (np.sum((a_arr >= 1024) & (a_arr < 9216)) / len(a_arr) * 100) if len(a_arr) else 0
        large_pct = (np.sum(a_arr >= 9216) / len(a_arr) * 100) if len(a_arr) else 0

        print(f"{cid:<3} {cname:<20} {avg_w:5.1f}x{avg_h:<5.1f} px   {med_area:6.0f} px²      {micro_pct:5.1f}%          {small_pct:5.1f}%          {large_pct:5.1f}%")

    print("\n--- Multi-Label Co-occurrence Analysis ---")
    co_occur = Counter()
    for img_name, cls_set in img_class_sets.items():
        if len(cls_set) > 1:
            cls_list = sorted(list(cls_set))
            for i in range(len(cls_list)):
                for j in range(i+1, len(cls_list)):
                    co_occur[(cls_list[i], cls_list[j])] += 1

    print("Top Co-occurring defect pairs in the same frame:")
    for (c1, c2), count in co_occur.most_common(8):
        print(f"  {classes[c1]} + {classes[c2]}: {count} images")

    print(f"\nSub-16x16 Extreme Micro-Boxes (<256 px²): {tiny_boxes_count}")
    print(f"Extreme Aspect Ratio BBoxes (>10:1 or <1:10): {len(extreme_aspect_boxes)}")

if __name__ == "__main__":
    run_analysis()
