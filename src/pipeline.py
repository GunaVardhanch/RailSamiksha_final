"""
Unified 4K Drone Defect Detection Pipeline for RailSamiksha
End-to-end integration: Video Frame -> Batched SAHI Slicing -> RT-DETR Inference ->
NMM Boundary Stitching -> ByteTrack Temporal Deduplication.
"""

from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import yaml
import numpy as np
import cv2

from src.sahi_slicer import SAHISlicer
from src.detector import RTDETRDetector
from src.postprocessor import PostProcessor
from src.tracker import DefectTracker

def load_yaml(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

class RailSamikshaPipeline:
    """
    Production inference pipeline executing batched SAHI slicing, RT-DETR detection,
    inter-patch NMM boundary stitching, and ByteTrack temporal deduplication.
    """

    def __init__(self, config_path: str = "configs/pipeline_config.yaml"):
        self.config_path = Path(config_path)
        self.config = load_yaml(self.config_path)

        sahi_cfg = self.config.get("sahi", {})
        det_cfg = self.config.get("detector", {})
        post_cfg = self.config.get("postprocess", {})
        track_cfg = self.config.get("tracker", {})
        ds_cfg = self.config.get("dataset", {})

        self.class_names = ds_cfg.get("classes", {})
        if isinstance(self.class_names, list):
            self.class_names = {i: name for i, name in enumerate(self.class_names)}

        # Initialize sub-modules
        self.slicer = SAHISlicer(
            slice_height=sahi_cfg.get("slice_height", 640),
            slice_width=sahi_cfg.get("slice_width", 640),
            overlap_height_ratio=sahi_cfg.get("overlap_height_ratio", 0.20),
            overlap_width_ratio=sahi_cfg.get("overlap_width_ratio", 0.20),
        )
        self.batch_size = sahi_cfg.get("batch_size", 8)
        self.perform_standard_pred = sahi_cfg.get("perform_standard_pred", True)

        self.detector = RTDETRDetector(
            weights_path=det_cfg.get("weights_path", "models/rtdetr-l.pt"),
            device=det_cfg.get("device", "cuda:0"),
            conf_threshold=det_cfg.get("confidence_threshold", 0.25),
            imgsz=det_cfg.get("imgsz", 640),
        )

        self.postprocessor = PostProcessor(
            iou_threshold=post_cfg.get("match_threshold", 0.50),
            merger_type=post_cfg.get("merger_type", "nmm"),
        )

        self.tracker = DefectTracker(
            track_thresh=track_cfg.get("track_thresh", 0.25),
            match_thresh=track_cfg.get("match_thresh", 0.80),
            min_consecutive_hits=track_cfg.get("min_consecutive_hits", 3),
        )

    def process_frame(
        self,
        frame: np.ndarray,
        frame_idx: int = 0,
        telemetry: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes complete inspection workflow on a single high-resolution drone frame.
        
        Args:
            frame: HxWxC BGR image (e.g. 3840x2160 or 2752x1536)
            frame_idx: Video frame index
            telemetry: Optional GPS coordinates dictionary
            
        Returns:
            Dict containing:
                - 'raw_detections': Global unstitched detections from all patches
                - 'merged_detections': Stitched NMM global bounding boxes
                - 'tracked_objects': Active ByteTrack track objects with persistent IDs
                - 'confirmed_alerts': Deduplicated confirmed defect alerts
        """
        h, w = frame.shape[:2]

        # 1. SAHI Slicing
        tiles, slice_boxes = self.slicer.slice_image(frame)

        # 2. Batched RT-DETR Inference
        raw_detections: List[Dict[str, Any]] = []
        for batch_array, batch_boxes in self.slicer.batch_slices(tiles, slice_boxes, batch_size=self.batch_size):
            batch_predictions = self.detector.predict_patches(batch_array)
            for patch_preds, sbox in zip(batch_predictions, batch_boxes):
                remapped = self.postprocessor.remap_to_global(patch_preds, sbox, frame_width=w, frame_height=h)
                raw_detections.extend(remapped)

        # Optional: Full frame coarse pass for large macro defects (e.g., extensive ballast issues)
        if self.perform_standard_pred:
            frame_preds = self.detector.predict_frame(frame)
            raw_detections.extend(frame_preds)

        # 3. Inter-Patch Non-Maximum Merging (NMM)
        merged_detections = self.postprocessor.merge_detections(raw_detections)

        # 4. ByteTrack Temporal Association & Flicker Filtering
        tracked_objects = self.tracker.update(merged_detections, frame_idx=frame_idx, telemetry=telemetry)
        confirmed_alerts = self.tracker.get_confirmed_alerts()

        # Add human-readable class names
        for det in merged_detections:
            det["class_name"] = self.class_names.get(det["class_id"], f"Class {det['class_id']}")
        for tobj in tracked_objects:
            tobj["class_name"] = self.class_names.get(tobj["class_id"], f"Class {tobj['class_id']}")

        return {
            "frame_idx": frame_idx,
            "raw_count": len(raw_detections),
            "merged_detections": merged_detections,
            "tracked_objects": tracked_objects,
            "confirmed_alerts": confirmed_alerts,
        }

    def annotate_frame(
        self,
        frame: np.ndarray,
        pipeline_output: Dict[str, Any],
        draw_tracks: bool = True,
    ) -> np.ndarray:
        """
        Renders bounding boxes, defect labels, track IDs, and alert badges onto frame.
        """
        annotated = frame.copy()
        items_to_draw = pipeline_output["tracked_objects"] if draw_tracks else pipeline_output["merged_detections"]

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

        for item in items_to_draw:
            box = item["box"]
            x1, y1, x2, y2 = map(int, box)
            cid = item["class_id"]
            cname = item.get("class_name", f"Class {cid}")
            score = item["score"]
            color = colors.get(cid, (0, 255, 0))

            tid_str = f" [ID:{item['track_id']}]" if "track_id" in item else ""
            status_str = " (CONFIRMED)" if item.get("is_confirmed") else ""
            label = f"{cname}{tid_str} {score:.2f}{status_str}"

            # Box
            thickness = 2 if not item.get("is_confirmed") else 3
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)

            # Label banner
            (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(annotated, (x1, max(0, y1 - th - baseline - 4)), (x1 + tw + 6, max(0, y1)), color, -1)
            cv2.putText(annotated, label, (x1 + 3, max(th + 2, y1 - baseline - 2)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        return annotated
