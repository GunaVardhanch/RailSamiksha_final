import numpy as np
from pathlib import Path
from collections import defaultdict

data_dir = Path("Dataset_consolidated/train/labels")
class_boxes = defaultdict(list)

for lbl in data_dir.glob("*.txt"):
    for line in lbl.read_text().splitlines():
        parts = line.strip().split()
        if len(parts) >= 5:
            cid = int(parts[0])
            w, h = float(parts[3]), float(parts[4])
            class_boxes[cid].append((w, h))

names = [
    "Ballast Defect", "Damaged Fastener", "Foreign Objects", "Missing Fastener", 
    "Rail Crack", "Rail Joint Damage", "Rail Misalignment", "Rail Wear", "Sleeper Defect"
]

print(f"{'ID':<3} {'Class Name':<20} {'Count':<6} {'Med W':<8} {'Med H':<8} {'Max W':<8} {'Max H':<8} {'Oversized (>0.35)'}")
print("-" * 85)
for cid in range(9):
    boxes = class_boxes[cid]
    if not boxes:
        continue
    ws = [b[0] for b in boxes]
    hs = [b[1] for b in boxes]
    oversized = sum(1 for w, h in boxes if w > 0.35 or h > 0.35)
    print(f"{cid:<3} {names[cid]:<20} {len(boxes):<6} {np.median(ws):<8.3f} {np.median(hs):<8.3f} {np.max(ws):<8.3f} {np.max(hs):<8.3f} {oversized} ({oversized/len(boxes)*100:.1f}%)")

