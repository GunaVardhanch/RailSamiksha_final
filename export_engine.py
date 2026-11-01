"""
TensorRT FP16 / ONNX Engine Exporter for RailSamiksha RT-DETR Detection
Compiles PyTorch checkpoints into high-throughput inference engines for RTX A4000.
"""

import argparse
from pathlib import Path
import torch
from ultralytics import RTDETR

def parse_args():
    parser = argparse.ArgumentParser(description="Export RT-DETR model to TensorRT engine / ONNX")
    parser.add_argument("--weights", type=str, default="models/rtdetr-l.pt", help="Path to input .pt weights")
    parser.add_argument("--format", type=str, default="engine", choices=["engine", "onnx"], help="Export format")
    parser.add_argument("--half", action="store_true", default=True, help="Enable FP16 half-precision")
    parser.add_argument("--imgsz", type=int, default=640, help="Input dimension")
    parser.add_argument("--device", type=str, default="0", help="CUDA device index")
    parser.add_argument("--batch", type=int, default=8, help="Max batch size for engine")
    return parser.parse_args()

def main():
    args = parse_args()
    weights_path = Path(args.weights)

    if not weights_path.exists():
        print(f"[ERROR] Weights file not found: {weights_path}")
        return

    print("=" * 80)
    print("RAILSAMIKSHA — MODEL EXPORT & OPTIMIZATION")
    print(f"Source Checkpoint: {weights_path}")
    print(f"Target Format:     {args.format.upper()}")
    print(f"Half Precision:    {args.half} (FP16)")
    print(f"Input Shape:       ({args.batch}, 3, {args.imgsz}, {args.imgsz})")
    print("=" * 80)

    model = RTDETR(str(weights_path))
    export_kwargs = {
        "format": args.format,
        "half": args.half,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "device": args.device if torch.cuda.is_available() else "cpu",
    }

    print("\nStarting engine compilation...")
    exported_path = model.export(**export_kwargs)
    print(f"\nExport complete! Optimized engine generated at: {exported_path}")

if __name__ == "__main__":
    main()
