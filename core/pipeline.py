"""
Unified RailSamiksha Production Pipeline
========================================
Integrates SAHI 1:1 scale patch slicing, RT-DETR-L deep detection,
Non-Maximum Merging (NMM), ByteTrack temporal deduplication, and telemetry georeferencing.
"""

import time
from typing import Dict, Any, List, Optional
import numpy as np
from core.detector import RTDETRDetector, annotate_detections
from core.slicer import SAHIPatchSlicer
from core.merger import NonMaximumMerger
from core.tracker import DefectTracker
from core.telemetry import TelemetrySimulator
from config import (
    DEFAULT_CONF,
    DEFAULT_SLICE_SIZE,
    DEFAULT_OVERLAP,
    DEFAULT_TEMPORAL_HITS
)


class RailSamikshaProductionPipeline:
    def __init__(
        self,
        weights_path: str,
        conf_threshold: float = DEFAULT_CONF,
        slice_size: int = DEFAULT_SLICE_SIZE,
        overlap_ratio: float = DEFAULT_OVERLAP,
        temporal_hits: int = DEFAULT_TEMPORAL_HITS,
        device: Optional[str] = None
    ):
        self.detector = RTDETRDetector(weights_path=weights_path, conf_threshold=conf_threshold, device=device)
        self.slicer = SAHIPatchSlicer(
            slice_height=slice_size,
            slice_width=slice_size,
            overlap_height_ratio=overlap_ratio,
            overlap_width_ratio=overlap_ratio
        )
        self.merger = NonMaximumMerger(match_threshold=0.45)
        self.tracker = DefectTracker(min_hits=temporal_hits)
        self.telemetry_sim = TelemetrySimulator()

    def set_confidence(self, conf: float):
        self.detector.conf_threshold = conf
        self.detector.model.overrides["conf"] = conf

    def reset_tracker(self):
        self.tracker = DefectTracker(min_hits=self.tracker.min_hits)

    def process_still_image(
        self,
        image: np.ndarray,
        use_sahi: bool = True
    ) -> Dict[str, Any]:
        """
        Executes complete inspection on a high-resolution drone orthophoto / still frame.
        """
        t0 = time.time()
        h, w = image.shape[:2]

        # On CPU cloud containers (Render Free 512MB RAM), use rapid direct inference (<1.5s, ~120MB RAM)
        # to guarantee zero HTTP 502/503 timeouts. Use full multi-patch SAHI on GPU/CUDA environments.
        is_cpu = str(getattr(self.detector, "device", "cpu")).lower() == "cpu"

        if use_sahi and not is_cpu and (h > 640 or w > 640):
            # Extract patches for GPU high-throughput slicing
            patches, bboxes = self.slicer.slice_image(image)
            patch_count = len(patches)

            # Batched detection
            batch_dets = self.detector.detect_batch(patches, imgsz=self.slicer.slice_height)

            # Remap local patch coordinates to global frame
            global_dets = []
            for (gx1, gy1, gx2, gy2), p_dets in zip(bboxes, batch_dets):
                for d in p_dets:
                    lx1, ly1, lx2, ly2 = d["box"]
                    d["box"] = [lx1 + gx1, ly1 + gy1, lx2 + gx1, ly2 + gy1]
                    global_dets.append(d)

            # Merge cross-tile duplicates
            merged_dets = self.merger.merge_detections(global_dets)
        else:
            patch_count = 1
            merged_dets = self.detector.detect_single(image, imgsz=640)

        elapsed_ms = (time.time() - t0) * 1000.0

        # Annotate
        annotated_img = annotate_detections(image, merged_dets)

        return {
            "annotated_image": annotated_img,
            "detections": merged_dets,
            "patch_count": patch_count,
            "latency_ms": elapsed_ms,
            "fps": 1000.0 / max(elapsed_ms, 1.0),
        }

    def process_video_frame(
        self,
        frame: np.ndarray,
        frame_idx: int,
        telemetry: Optional[Dict[str, Any]] = None,
        use_sahi_for_video: bool = False
    ) -> Dict[str, Any]:
        """
        Processes a single patrol video frame with temporal deduplication.
        """
        t0 = time.time()

        if telemetry is None:
            telemetry = self.telemetry_sim.get_frame_telemetry(frame_idx)

        # In video mode, single pass is used for speed unless SAHI is explicitly requested
        if use_sahi_for_video:
            res = self.process_still_image(frame, use_sahi=True)
            raw_dets = res["detections"]
        else:
            raw_dets = self.detector.detect_single(frame, imgsz=640)

        # Associate with temporal tracker
        tracked_dets = self.tracker.update(raw_dets, frame_idx, telemetry)
        elapsed_ms = (time.time() - t0) * 1000.0

        # Render annotations
        annotated_frame = annotate_detections(frame, tracked_dets)

        return {
            "annotated_frame": annotated_frame,
            "detections": tracked_dets,
            "active_tracks_count": len(self.tracker.active_tracks),
            "verified_incidents": self.tracker.get_verified_incidents(),
            "telemetry": telemetry,
            "latency_ms": elapsed_ms,
            "fps": 1000.0 / max(elapsed_ms, 1.0)
        }

