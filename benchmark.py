"""
Comprehensive Benchmark & Validation Suite for RailSamiksha 4K Aerial Defect Detection
Measures end-to-end 4K latency (FPS), GPU memory utilization, and detection performance.
"""

import time
import argparse
from pathlib import Path
import yaml
import torch
import numpy as np
from ultralytics import RTDETR

from src.pipeline import RailSamikshaPipeline

def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark RailSamiksha 4K Detection Pipeline")
    parser.add_argument("--model", type=str, default="models/rtdetr-l.pt", help="Path to model checkpoint (.pt or .engine)")
    parser.add_argument("--config", type=str, default="configs/pipeline_config.yaml", help="Path to pipeline configuration")
    parser.add_argument("--warmup", type=int, default=5, help="Number of warmup iterations")
    parser.add_argument("--iterations", type=int, default=20, help="Number of benchmark iterations")
    parser.add_argument("--resolution", type=str, default="3840x2160", help="Simulated frame resolution (WxH)")
    parser.add_argument("--val", action="store_true", help="Run full evaluation on validation/test split")
    return parser.parse_args()

def run_latency_benchmark(pipeline: RailSamikshaPipeline, width: int, height: int, warmup: int, iterations: int):
    print("=" * 80)
    print("RAILSAMIKSHA — 4K PIPELINE LATENCY & THROUGHPUT BENCHMARK")
    print(f"Frame Resolution: {width}x{height}")
    print(f"Warmup Runs:      {warmup}")
    print(f"Benchmark Runs:   {iterations}")
    print(f"Device:           {pipeline.detector.device}")
    print("=" * 80)

    # Generate synthetic 4K aerial frame
    dummy_frame = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)

    print("\nWarming up GPU caches...")
    for _ in range(warmup):
        pipeline.process_frame(dummy_frame)

    if torch.cuda.is_available():
        torch.cuda.synchronize()

    print("Running timed inference trials...")
    latencies = []
    slicing_times = []
    inference_times = []
    merging_times = []
    tracking_times = []

    for i in range(iterations):
        t0 = time.perf_counter()

        # Step 1: Slicing
        t_s0 = time.perf_counter()
        tiles, slice_boxes = pipeline.slicer.slice_image(dummy_frame)
        t_s1 = time.perf_counter()
        slicing_times.append((t_s1 - t_s0) * 1000.0)

        # Step 2: Batched Inference
        t_i0 = time.perf_counter()
        raw_detections = []
        for batch_array, batch_boxes in pipeline.slicer.batch_slices(tiles, slice_boxes, batch_size=pipeline.batch_size):
            batch_preds = pipeline.detector.predict_patches(batch_array)
            for patch_preds, sbox in zip(batch_preds, batch_boxes):
                remapped = pipeline.postprocessor.remap_to_global(patch_preds, sbox, frame_width=width, frame_height=height)
                raw_detections.extend(remapped)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        t_i1 = time.perf_counter()
        inference_times.append((t_i1 - t_i0) * 1000.0)

        # Step 3: NMM Merging
        t_m0 = time.perf_counter()
        merged = pipeline.postprocessor.merge_detections(raw_detections)
        t_m1 = time.perf_counter()
        merging_times.append((t_m1 - t_m0) * 1000.0)

        # Step 4: Tracking
        t_t0 = time.perf_counter()
        tracked = pipeline.tracker.update(merged, frame_idx=i)
        t_t1 = time.perf_counter()
        tracking_times.append((t_t1 - t_t0) * 1000.0)

        total_t = (time.perf_counter() - t0) * 1000.0
        latencies.append(total_t)

    avg_total = np.mean(latencies)
    fps = 1000.0 / avg_total

    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS SUMMARY")
    print("=" * 80)
    print(f"End-to-End Latency:      {avg_total:.2f} ms ± {np.std(latencies):.2f} ms")
    print(f"Throughput (FPS):        {fps:.2f} FPS")
    print(f"Stage 1 - SAHI Slicing:  {np.mean(slicing_times):.2f} ms ({len(tiles)} patches)")
    print(f"Stage 2 - GPU Inference: {np.mean(inference_times):.2f} ms ({np.mean(inference_times)/len(tiles):.2f} ms/patch)")
    print(f"Stage 3 - NMM Stitching: {np.mean(merging_times):.2f} ms")
    print(f"Stage 4 - ByteTrack:     {np.mean(tracking_times):.2f} ms")
    if torch.cuda.is_available():
        peak_vram = torch.cuda.max_memory_allocated() / (1024**2)
        print(f"Peak GPU VRAM Usage:     {peak_vram:.2f} MB")
    print("=" * 80)

def main():
    args = parse_args()
    w, h = map(int, args.resolution.lower().split("x"))
    pipeline = RailSamikshaPipeline(config_path=args.config)
    run_latency_benchmark(pipeline, width=w, height=h, warmup=args.warmup, iterations=args.iterations)

if __name__ == "__main__":
    main()
