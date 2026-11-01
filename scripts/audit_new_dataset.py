import os
import glob
from pathlib import Path
from collections import Counter
import cv2

DATASET_DIR = Path(r"c:\Users\Administrator\Desktop\RailSamiksha_Drone_defect_detection_Project\Dats set final version part 1.1")

splits = ["train", "valid", "test"]
print("=== AUDIT OF FINAL_DATASET_VERSION_PART_1 ===")

total_images = 0
total_labels = 0
resolutions = Counter()
class_counter = Counter()
empty_images_count = 0

for split in splits:
    img_dir = DATASET_DIR / split / "images"
    lbl_dir = DATASET_DIR / split / "labels"
    
    img_files = glob.glob(str(img_dir / "*.*"))
    lbl_files = glob.glob(str(lbl_dir / "*.txt"))
    
    print(f"\nSplit '{split}': {len(img_files)} images, {len(lbl_files)} label files")
    total_images += len(img_files)
    
    split_class_counter = Counter()
    split_empty_count = 0
    
    for img_path in img_files:
        p = Path(img_path)
        lbl_path = lbl_dir / f"{p.stem}.txt"
        
        # sample resolution check
        if len(resolutions) < 20:
            img = cv2.imread(img_path)
            if img is not None:
                h, w = img.shape[:2]
                resolutions[(w, h)] += 1
                
        if not lbl_path.exists():
            split_empty_count += 1
            empty_images_count += 1
            continue
            
        with open(lbl_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            
        if len(lines) == 0:
            split_empty_count += 1
            empty_images_count += 1
        else:
            for line in lines:
                parts = line.split()
                if parts:
                    cls_id = int(parts[0])
                    split_class_counter[cls_id] += 1
                    class_counter[cls_id] += 1
                    total_labels += 1
                    
    print(f"  Empty/Negative samples in {split}: {split_empty_count}")
    print(f"  Class counts in {split}: {dict(sorted(split_class_counter.items()))}")

print("\n=== TOTAL SUMMARY ===")
print(f"Total Images: {total_images}")
print(f"Total Defect Bounding Boxes: {total_labels}")
print(f"Total Negative/Empty Images: {empty_images_count}")
print(f"Image Resolutions Sampled: {dict(resolutions)}")
print(f"Overall Class Distribution (Raw IDs): {dict(sorted(class_counter.items()))}")
