"""
Visualizer for RailSamiksha Ground Truth Bounding Box Annotations
Draws defect bounding boxes on sample high-resolution images to verify label alignments.
"""

from pathlib import Path
import random
import cv2
import yaml

def load_yaml(yaml_path: Path):
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    root = Path(__file__).resolve().parent.parent
    data_dir = root / "data"
    yaml_path = root / "configs" / "dataset.yaml"
    out_dir = root / "reports" / "sample_annotations"
    out_dir.mkdir(parents=True, exist_ok=True)

    config = load_yaml(yaml_path)
    class_names = config.get("names", {})
    if isinstance(class_names, list):
        class_names = {i: name for i, name in enumerate(class_names)}

    # Distinct vibrant colors per class for inspection
    colors = {
        0: (0, 165, 255),    # Ballast Defect (Orange)
        1: (0, 0, 255),      # Damaged Fastener (Red)
        2: (255, 255, 0),    # Foreign Objects (Cyan)
        3: (255, 0, 255),    # Missing Fastener (Magenta)
        4: (0, 255, 255),    # Rail Crack (Yellow)
        5: (128, 0, 255),    # Rail Joint Damage (Violet)
        6: (255, 128, 0),    # Rail Misalignment (Blue)
        7: (0, 255, 0),      # Rail Wear (Green)
        8: (255, 0, 0),      # Sleeper Defect (Dark Blue)
    }

    train_img_dir = data_dir / "train" / "images"
    train_lbl_dir = data_dir / "train" / "labels"

    # Find sample images for key classes
    class_to_samples = {cid: [] for cid in range(len(class_names))}
    for lbl_file in sorted(train_lbl_dir.glob("*.txt")):
        with open(lbl_file, "r") as f:
            lines = [l.strip() for l in f if l.strip()]
        for line in lines:
            cid = int(line.split()[0])
            img_file = train_img_dir / f"{lbl_file.stem}.jpg"
            if img_file.exists() and img_file not in class_to_samples[cid]:
                class_to_samples[cid].append(img_file)

    selected_images = set()
    for cid, imgs in class_to_samples.items():
        if imgs:
            selected_images.add(imgs[0])
            if len(imgs) > 1:
                selected_images.add(imgs[1])

    # Limit to top 8 distinct images for fast generation
    selected_images = list(selected_images)[:8]
    print(f"Rendering ground truth bounding boxes on {len(selected_images)} sample images...")

    for img_path in selected_images:
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        h, w = img.shape[:2]
        lbl_path = train_lbl_dir / f"{img_path.stem}.txt"

        if lbl_path.exists():
            with open(lbl_path, "r") as f:
                lines = [l.strip() for l in f if l.strip()]

            for line in lines:
                parts = line.split()
                cid = int(parts[0])
                xc, yc, bw, bh = map(float, parts[1:5])

                x1 = int((xc - bw / 2.0) * w)
                y1 = int((yc - bh / 2.0) * h)
                x2 = int((xc + bw / 2.0) * w)
                y2 = int((yc + bh / 2.0) * h)

                cname = class_names.get(cid, f"Class {cid}")
                color = colors.get(cid, (0, 255, 0))

                # Draw bounding box
                thickness = max(2, int(min(w, h) / 500))
                cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)

                # Draw label banner
                label = f"{cname}"
                font_scale = max(0.5, min(w, h) / 1200)
                (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)
                cv2.rectangle(img, (x1, max(0, y1 - th - baseline - 6)), (x1 + tw + 6, max(0, y1)), color, -1)
                cv2.putText(img, label, (x1 + 3, max(th + 2, y1 - baseline - 2)), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), 2)

        out_path = out_dir / f"annotated_{img_path.name}"
        cv2.imwrite(str(out_path), img)
        print(f"  -> Saved: {out_path.name}")

    print(f"\nSample annotations saved to {out_dir}")

if __name__ == "__main__":
    main()
