"""
Script to rebalance the test split by shifting selected images and paired labels
for minority classes (Damaged Fastener [ID 1] and Rail Misalignment [ID 6]).
"""

import shutil
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    data_dir = root / "data"

    train_img_dir = data_dir / "train" / "images"
    train_lbl_dir = data_dir / "train" / "labels"
    test_img_dir = data_dir / "test" / "images"
    test_lbl_dir = data_dir / "test" / "labels"

    # Selected candidate images that contain pure class 1 and class 6 instances
    candidates_to_move = [
        # Class 1: Damaged Fastener (3 instances + 1 instance = 4 instances total to test)
        "Gemini_Generated_Image_dleuihdleuihdleu_png.rf.89397b611a2a32b4119713795577066a",
        "missing_fastener_007_png.rf.187c6735e350b0c455c8739829a0a849",
        # Class 6: Rail Misalignment (1 instance + 1 instance = 2 instances total to test)
        "3ee3e7ac-8752-4868-bbca-543e4c6bcd46_png.rf.93b99f22685aca965c3eaebd032ec52b",
        "42909d3a-757f-42d9-a404-d92c25e86424_png.rf.040cad706f05ac4f13b1381be1cd52e1"
    ]

    print(f"Transferring {len(candidates_to_move)} image-label pairs from 'train' to 'test'...")

    moved_count = 0
    for stem in candidates_to_move:
        src_img = train_img_dir / f"{stem}.jpg"
        src_lbl = train_lbl_dir / f"{stem}.txt"
        dst_img = test_img_dir / f"{stem}.jpg"
        dst_lbl = test_lbl_dir / f"{stem}.txt"

        if not src_img.exists():
            print(f"[ERROR] Source image not found: {src_img}")
            continue
        if not src_lbl.exists():
            print(f"[ERROR] Source label not found: {src_lbl}")
            continue

        # Move files
        shutil.move(str(src_img), str(dst_img))
        shutil.move(str(src_lbl), str(dst_lbl))

        # Verify destination
        if dst_img.exists() and dst_lbl.exists():
            print(f"  [SUCCESS] Moved {stem} -> test/images and test/labels")
            moved_count += 1
        else:
            print(f"  [ERROR] Verification failed for {stem}")

    print(f"\nCompleted! {moved_count}/{len(candidates_to_move)} pairs successfully transferred to test set.")

if __name__ == "__main__":
    main()
