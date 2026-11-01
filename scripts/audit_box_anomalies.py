"""
Deep Annotation Topology & Scale Anomaly Auditor
=================================================
Audits Dataset_consolidated across train, valid, and test splits:
- Isolates full-tie macro-boxes in Sleeper Defect (Class 8).
- Detects oversized baseplate vs microscopic clip boxes in Fasteners (Classes 1 & 3).
- Evaluates Rail Crack (Class 4) and Rail Joint Damage (Class 5) scale consistency.
- Exports a detailed anomaly breakdown and highlights top offending files.
"""

from pathlib import Path
from collections import defaultdict
import numpy as np
import pandas as pd
import cv2

DATASET_DIR = Path("Dataset_consolidated")
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

def audit_dataset():
    records = []
    anomalies_by_file = defaultdict(list)
    class_stats = {cid: [] for cid in range(9)}

    for split in ["train", "valid", "test"]:
        lbl_dir = DATASET_DIR / split / "labels"
        img_dir = DATASET_DIR / split / "images"

        if not lbl_dir.exists():
            continue

        for lbl_file in sorted(lbl_dir.glob("*.txt")):
            lines = lbl_file.read_text(encoding="utf-8").strip().splitlines()
            for line_idx, line in enumerate(lines):
                parts = line.strip().split()
                if len(parts) < 5:
                    continue

                cid = int(parts[0])
                xc, yc, bw, bh = [float(p) for p in parts[1:5]]
                area = bw * bh
                aspect_ratio = bw / max(bh, 1e-6)

                class_stats[cid].append({
                    "split": split,
                    "file": lbl_file.stem,
                    "w": bw,
                    "h": bh,
                    "area": area,
                    "aspect_ratio": aspect_ratio
                })

                # Check for specific class anomalies
                is_anomaly = False
                anomaly_type = []

                # Class 8: Sleeper Defect
                if cid == 8:
                    if bw > 0.35 or bh > 0.35 or area > 0.10:
                        is_anomaly = True
                        anomaly_type.append(f"Oversized Macro-Tie Box (w={bw:.2f}, h={bh:.2f}, area={area:.3f})")
                    elif bw < 0.02 and bh < 0.02:
                        is_anomaly = True
                        anomaly_type.append(f"Microscopic Noise (w={bw:.3f}, h={bh:.3f})")

                # Class 1 & 3: Fasteners (Damaged & Missing)
                elif cid in (1, 3):
                    cname = CANONICAL_NAMES[cid]
                    if bw > 0.15 or bh > 0.15:
                        is_anomaly = True
                        anomaly_type.append(f"Oversized Fastener (Enclosing Baseplate/Tie, w={bw:.2f}, h={bh:.2f})")
                    elif bw < 0.015 or bh < 0.015:
                        is_anomaly = True
                        anomaly_type.append(f"Sub-Pixel Micro Fastener (w={bw:.3f}, h={bh:.3f})")

                # Class 4: Rail Crack
                elif cid == 4:
                    if bw > 0.40 or bh > 0.40:
                        is_anomaly = True
                        anomaly_type.append(f"Oversized Rail Crack (w={bw:.2f}, h={bh:.2f})")
                    elif area < 0.0005:
                        is_anomaly = True
                        anomaly_type.append(f"Sub-visible Micro-Crack (area={area:.5f})")

                # Class 5: Rail Joint Damage
                elif cid == 5:
                    if bw > 0.40 or bh > 0.40:
                        is_anomaly = True
                        anomaly_type.append(f"Oversized Joint Box (w={bw:.2f}, h={bh:.2f})")

                if is_anomaly:
                    anomalies_by_file[lbl_file.stem].append({
                        "split": split,
                        "class_id": cid,
                        "class_name": CANONICAL_NAMES[cid],
                        "box": (xc, yc, bw, bh),
                        "reasons": anomaly_type
                    })

    print("=" * 95)
    print("  [RAIL SAMIKSHA] ANNOTATION TOPOLOGY & SCALE ANOMALY AUDIT (DATASET_CONSOLIDATED)")
    print("=" * 95)

    summary_rows = []
    for cid in range(9):
        boxes = class_stats[cid]
        cname = CANONICAL_NAMES[cid]
        total_boxes = len(boxes)
        if total_boxes == 0:
            continue

        ws = [b["w"] for b in boxes]
        hs = [b["h"] for b in boxes]
        areas = [b["area"] for b in boxes]

        # Calculate anomaly counts
        if cid == 8:
            anom_count = sum(1 for b in boxes if b["w"] > 0.35 or b["h"] > 0.35 or b["area"] > 0.10)
        elif cid in (1, 3):
            anom_count = sum(1 for b in boxes if b["w"] > 0.15 or b["h"] > 0.15 or b["w"] < 0.015 or b["h"] < 0.015)
        elif cid == 4:
            anom_count = sum(1 for b in boxes if b["w"] > 0.40 or b["h"] > 0.40 or b["area"] < 0.0005)
        elif cid == 5:
            anom_count = sum(1 for b in boxes if b["w"] > 0.40 or b["h"] > 0.40)
        else:
            anom_count = sum(1 for b in boxes if b["w"] > 0.50 or b["h"] > 0.50)

        anom_pct = (anom_count / total_boxes) * 100.0

        summary_rows.append({
            "CID": cid,
            "Class Name": cname,
            "Total Boxes": total_boxes,
            "Med W": np.median(ws),
            "Med H": np.median(hs),
            "Max W": np.max(ws),
            "Max H": np.max(hs),
            "Anomalous Boxes": f"{anom_count} ({anom_pct:.1f}%)"
        })

    df_summary = pd.DataFrame(summary_rows)
    print(f"\n{'CID':<4} {'Class Name':<20} {'Count':<7} {'Med W':<8} {'Med H':<8} {'Max W':<8} {'Max H':<8} {'Anomalies (Flagged)'}")
    print("-" * 95)
    for row in summary_rows:
        print(f"{row['CID']:<4} {row['Class Name']:<20} {row['Total Boxes']:<7} {row['Med W']:<8.3f} {row['Med H']:<8.3f} {row['Max W']:<8.3f} {row['Max H']:<8.3f} {row['Anomalous Boxes']}")

    total_flagged_files = len(anomalies_by_file)
    total_flagged_boxes = sum(len(v) for v in anomalies_by_file.values())
    print("\n" + "=" * 95)
    print(f"Total Unique Images with Annotation Scale Flaws: {total_flagged_files}")
    print(f"Total Bounding Boxes Requiring Refinement:       {total_flagged_boxes}")
    print("=" * 95)

    # Show top 10 worst offending images
    sorted_files = sorted(anomalies_by_file.items(), key=lambda kv: len(kv[1]), reverse=True)
    print("\nTop 10 Images with Most Severe Annotation Conflicts:")
    print(f"{'Image Stem':<45} {'Split':<8} {'Anomaly Count':<14} {'Defect Classes Involved'}")
    print("-" * 95)
    for stem, anom_list in sorted_files[:10]:
        split = anom_list[0]["split"]
        classes = sorted(list(set(a["class_name"] for a in anom_list)))
        print(f"{stem:<45} {split:<8} {len(anom_list):<14} {', '.join(classes)}")

    return df_summary, anomalies_by_file

if __name__ == "__main__":
    audit_dataset()
