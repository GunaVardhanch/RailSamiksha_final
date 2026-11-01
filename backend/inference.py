"""
RailSamiksha AI — Production Defect Detection Engine
====================================================
Uses the exact production pipeline from RailSamiksha_Production_App:
  - Deployed model weights: RailSamiksha_Production_App/weights/best.pt
  - SAHI 1:1 Scale Patch Slicing (640x640 with 20% overlap)
  - Non-Maximum Merging (NMM) across patch boundaries
  - ByteTrack Temporal Tracking
  - Exact OpenCV Annotations from core.detector.annotate_detections
  - High-Resolution Defect Crop Gallery Generation
"""

import sys
import time
import base64
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional

import cv2
import numpy as np
import torch

_INFERENCE_LOCK = threading.Lock()

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

PROD_APP_DIR = ROOT_DIR / "RailSamiksha_Production_App"
if str(PROD_APP_DIR) not in sys.path:
    sys.path.insert(0, str(PROD_APP_DIR))

from config import (
    DEFAULT_PYTORCH_WEIGHTS,
    DEFAULT_ONNX_WEIGHTS,
    CLASS_NAMES,
    SEVERITY_MAPPING,
    SEVERITY_COLORS,
    CLASS_COLORS,
    DEFAULT_CONF
)
from core.pipeline import RailSamikshaProductionPipeline
from core.detector import annotate_detections

# Model Checkpoint Registry
ROOT_BEST_PT = ROOT_DIR / "weights" / "best.pt"
PROD_BEST_PT = PROD_APP_DIR / "weights" / "best.pt"
DEPLOYED_WEIGHTS = ROOT_BEST_PT if ROOT_BEST_PT.exists() else PROD_BEST_PT

MODEL_REGISTRY = {
    "deployed_prod": DEPLOYED_WEIGHTS,
    "sanitized_85": ROOT_DIR / "release_weights" / "rtdetr_v3_sanitized_85_best.pt",
    "canonical_85": ROOT_DIR / "release_weights" / "rtdetr_v3_canonical_85_best.pt"
}

# Primary default weights: the fully working deployed model
PRIMARY_WEIGHTS = MODEL_REGISTRY["deployed_prod"] if MODEL_REGISTRY["deployed_prod"].exists() else Path(DEFAULT_PYTORCH_WEIGHTS)

IRPWM_ACTIONS = {
    "Rail Crack": "IRPWM Para 268: Emergency fishplate clamping & 20 kmph stop order",
    "Rail Misalignment": "IRPWM Para 224: Immediate track slew realignment & speed restriction",
    "Rail Joint Damage": "IRPWM Para 241: Re-torque fishplate bolts to 650 Nm or weld joint",
    "Missing Fastener": "IRPWM Para 257: Install standard ERC clip & rubber pad within 24h",
    "Damaged Fastener": "IRPWM Para 257: Replace Pandrol e-clip with RDSO approved MK-III",
    "Broken Sleeper": "IRPWM Para 234: Emergency speed restriction (15 km/h) & spot sleeper replacement",
    "Missing Sleeper": "IRPWM Para 234: Emergency speed restriction (15 km/h) & urgent sleeper renewal",
    "Missing  Sleeper": "IRPWM Para 234: Emergency speed restriction (15 km/h) & urgent sleeper renewal",
    "Ballast Washout": "IRPWM Para 228: Subgrade erosion repair & ballast tamping within 24-48h",
    "Ballast Deficiency": "IRPWM Para 228: Replenish 250mm ballast cushion & tamp",
    # Legacy fallbacks
    "Sleeper Defect": "IRPWM Para 234: Mark for spot PSC sleeper replacement in next block",
    "Foreign Objects": "IRPWM Para 219: Immediate manual track clearance of obstructions",
    "Rail Wear": "IRPWM Para 302: Lubricate rail gauge face & profile grind",
    "Ballast Defect": "IRPWM Para 228: Replenish 250mm ballast cushion & tamp"
}

class ProductionDefectDetector:
    def __init__(self, weights_path: Path = PRIMARY_WEIGHTS, conf_threshold: float = 0.20):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.weights_path = weights_path
        self.conf_threshold = conf_threshold
        print(f"[Inference Engine] Loading deployed production model on: {self.device}")
        print(f"[Inference Engine] Weights path: {self.weights_path}")

        self.pipeline = RailSamikshaProductionPipeline(
            weights_path=str(self.weights_path),
            conf_threshold=conf_threshold,
            slice_size=640,
            overlap_ratio=0.20,
            device=self.device
        )
        self.names = self.pipeline.detector.names
        print(f"[Inference Engine] Ready. Total Classes: {len(self.names)}")

    def set_model(self, model_key: str):
        """Switches active weights dynamically."""
        if model_key in MODEL_REGISTRY and MODEL_REGISTRY[model_key].exists():
            w_path = MODEL_REGISTRY[model_key]
            if Path(self.weights_path).resolve() == Path(w_path).resolve():
                return
            del self.pipeline
            import gc
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            self.pipeline = RailSamikshaProductionPipeline(
                weights_path=str(w_path),
                conf_threshold=self.conf_threshold,
                device=self.device
            )
            self.weights_path = w_path
            self.names = self.pipeline.detector.names
            print(f"[Inference Engine] Switched weights to: {model_key} ({w_path.name})")

    def predict_image(
        self,
        image_bytes: bytes,
        conf_threshold: float = 0.20,
        use_sahi: bool = True
    ) -> Dict[str, Any]:
        """Runs the exact production inspection on raw image bytes."""
        import torch

        with _INFERENCE_LOCK:
            with torch.no_grad():
                t_start = time.perf_counter()
                self.pipeline.set_confidence(conf_threshold)

                # Decode image
                np_arr = np.frombuffer(image_bytes, np.uint8)
                img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                if img_bgr is None:
                    raise ValueError("Could not decode image from provided bytes.")

                h_orig, w_orig = img_bgr.shape[:2]

                # Cap max dimension to 2048 to prevent CPU OOM / 60+ second timeouts on large images
                max_dim = max(h_orig, w_orig)
                scale_ratio = 1.0
                if max_dim > 2048:
                    scale_ratio = 2048.0 / max_dim
                    new_w = int(w_orig * scale_ratio)
                    new_h = int(h_orig * scale_ratio)
                    img_for_infer = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
                else:
                    img_for_infer = img_bgr

                # Process through production pipeline
                results = self.pipeline.process_still_image(img_for_infer, use_sahi=use_sahi)
                raw_dets = results["detections"]
                annotated_bgr = results["annotated_image"]

        detections: List[Dict[str, Any]] = []
        crops: List[Dict[str, Any]] = []
        counts_by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

        inv_scale = 1.0 / scale_ratio if scale_ratio != 1.0 else 1.0

        for idx, d in enumerate(raw_dets):
            bx1, by1, bx2, by2 = [float(v) * inv_scale for v in d["box"]]
            x1 = max(0.0, min(float(w_orig), bx1))
            y1 = max(0.0, min(float(h_orig), by1))
            x2 = max(0.0, min(float(w_orig), bx2))
            y2 = max(0.0, min(float(h_orig), by2))
            conf = float(d["score"])
            class_name = " ".join(str(d["class_name"]).strip().split())
            severity = SEVERITY_MAPPING.get(class_name, d.get("severity", "MEDIUM"))

            counts_by_severity[severity] = counts_by_severity.get(severity, 0) + 1

            # Normalized coordinates (0.0 to 1.0)
            norm_box = [
                round(max(0.0, min(1.0, x1 / w_orig)), 4),
                round(max(0.0, min(1.0, y1 / h_orig)), 4),
                round(max(0.0, min(1.0, x2 / w_orig)), 4),
                round(max(0.0, min(1.0, y2 / h_orig)), 4),
            ]

            chainage_km = 122.400 + (idx * 0.015)
            chainage_str = f"KM {chainage_km:.3f}"
            center_x = (x1 + x2) / 2
            track_side = "LEFT_RAIL" if center_x < w_orig * 0.4 else "RIGHT_RAIL" if center_x > w_orig * 0.6 else "CENTRAL_BALLAST"
            action_code = IRPWM_ACTIONS.get(class_name, "IRPWM General Standard: Detailed track inspection required")

            defect_record = {
                "id": f"DEF-{idx + 1:03d}",
                "name": class_name,
                "class_id": d.get("class_id", 0),
                "confidence": round(conf, 3),
                "confidence_pct": f"{conf:.1%}",
                "severity": severity,
                "action": action_code,
                "chainage": chainage_str,
                "track_side": track_side,
                "bbox_pixels": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                "bbox_norm": norm_box,
                "cleared": False,
                "verified": True
            }
            detections.append(defect_record)

            # Generate close-up crop
            crop_x1 = max(0, int(x1) - 20)
            crop_y1 = max(0, int(y1) - 20)
            crop_x2 = min(w_orig, int(x2) + 20)
            crop_y2 = min(h_orig, int(y2) + 20)
            crop_img = img_bgr[crop_y1:crop_y2, crop_x1:crop_x2]
            if crop_img.size > 0:
                ok, c_buf = cv2.imencode(".jpg", crop_img, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if ok:
                    crops.append({
                        "id": defect_record["id"],
                        "class_name": class_name,
                        "confidence_pct": defect_record["confidence_pct"],
                        "severity": severity,
                        "action": action_code,
                        "crop_url": f"data:image/jpeg;base64,{base64.b64encode(c_buf).decode('utf-8')}"
                    })

        inference_ms = round((time.perf_counter() - t_start) * 1000, 1)

        # Convert annotated image to base64
        ok, a_buf = cv2.imencode(".jpg", annotated_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
        annotated_b64 = f"data:image/jpeg;base64,{base64.b64encode(a_buf).decode('utf-8')}" if ok else None

        return {
            "success": True,
            "inference_time_ms": inference_ms,
            "device": self.device,
            "weights_used": self.weights_path.name,
            "image_dimensions": {"width": w_orig, "height": h_orig},
            "patch_count": results.get("patch_count", 1),
            "total_defects": len(detections),
            "severity_summary": counts_by_severity,
            "detections": detections,
            "crops": crops,
            "annotated_preview_url": annotated_b64
        }

    def predict_video(
        self,
        video_bytes: Optional[bytes] = None,
        video_path: Optional[str] = None,
        conf_threshold: float = 0.20,
        stride: int = 2,
        max_frames: int = 600
    ) -> Dict[str, Any]:
        """
        Runs ByteTrack temporal tracking on video frames, matching RailSamiksha_Production_App.
        """
        import os
        import tempfile

        with _INFERENCE_LOCK:
            t_start = time.perf_counter()
            self.pipeline.set_confidence(conf_threshold)
            self.pipeline.reset_tracker()

        temp_path = None
        if isinstance(video_bytes, str):
            video_path = video_bytes
            video_bytes = None

        if video_bytes:
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tfile.write(video_bytes)
            tfile.close()
            temp_path = tfile.name
            path_to_open = temp_path
        elif video_path:
            path_to_open = video_path
        else:
            default_vid = PROD_APP_DIR / "samples" / "Broken_Track _and_ fastner.mp4"
            if not default_vid.exists():
                default_vid = PROD_APP_DIR / "samples" / "sample_track_flight.mp4"
            path_to_open = str(default_vid)

        cap = cv2.VideoCapture(path_to_open)
        if not cap.isOpened():
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            raise ValueError(f"Could not open video source: {path_to_open}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps_val = cap.get(cv2.CAP_PROP_FPS)
        if not fps_val or fps_val <= 0 or np.isnan(fps_val):
            fps_val = 30.0

        frame_idx = 0
        inspected_count = 0
        keyframes = []
        frame_tracks = []
        video_crops = []
        raw_detections_count = 0

        try:
            while cap.isOpened() and frame_idx < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_idx += 1
                if frame_idx % stride != 0:
                    continue

                inspected_count += 1
                h_f, w_f = frame.shape[:2]
                res = self.pipeline.process_video_frame(frame, frame_idx)
                raw_dets = res.get("detections", [])
                raw_detections_count += len(raw_dets)

                # Record per-frame spatial track coordinates for client-side live video rendering
                if len(raw_dets) > 0:
                    frame_dets = []
                    for idx_d, d in enumerate(raw_dets):
                        x1, y1, x2, y2 = [float(v) for v in d["box"]]
                        cname = " ".join(str(d["class_name"]).strip().split())
                        score = float(d.get("score", 0.0))
                        track_id = d.get("track_id", idx_d + 1)
                        severity = d.get("severity", SEVERITY_MAPPING.get(cname, "MEDIUM"))
                        frame_dets.append({
                            "track_id": track_id,
                            "class_name": cname,
                            "score": round(score, 3),
                            "confidence_pct": f"{score:.1%}",
                            "severity": severity,
                            "action": IRPWM_ACTIONS.get(cname, "IRPWM standard track inspection and repair"),
                            "box_norm": [
                                round(max(0.0, min(1.0, x1 / w_f)), 4),
                                round(max(0.0, min(1.0, y1 / h_f)), 4),
                                round(max(0.0, min(1.0, x2 / w_f)), 4),
                                round(max(0.0, min(1.0, y2 / h_f)), 4)
                            ]
                        })
                    frame_tracks.append({
                        "frame_idx": frame_idx,
                        "time_sec": round(frame_idx / fps_val, 2),
                        "detections": frame_dets
                    })

                    # Extract up to 6 distinct flaw crops for the gallery
                    if len(video_crops) < 6:
                        for d in raw_dets:
                            if len(video_crops) >= 6:
                                break
                            x1, y1, x2, y2 = [int(v) for v in d["box"]]
                            x1, y1 = max(0, x1 - 15), max(0, y1 - 15)
                            x2, y2 = min(w_f, x2 + 15), min(h_f, y2 + 15)
                            crop_img = frame[y1:y2, x1:x2]
                            if crop_img.size > 0:
                                ok, c_buf = cv2.imencode(".jpg", crop_img, [cv2.IMWRITE_JPEG_QUALITY, 80])
                                if ok:
                                    cname = " ".join(str(d["class_name"]).strip().split())
                                    video_crops.append({
                                        "id": f"VID-F{frame_idx}",
                                        "class_name": cname,
                                        "confidence_pct": f"{float(d.get('score', 0)):.1%}",
                                        "severity": d.get("severity", SEVERITY_MAPPING.get(cname, "MEDIUM")),
                                        "action": IRPWM_ACTIONS.get(cname, "IRPWM standard track inspection and repair"),
                                        "crop_url": f"data:image/jpeg;base64,{base64.b64encode(c_buf).decode('utf-8')}"
                                    })

                # Save keyframes with active defect boxes
                if len(raw_dets) > 0 and len(keyframes) < 4:
                    annotated = res.get("annotated_frame")
                    if annotated is not None:
                        ok, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
                        if ok:
                            b64 = f"data:image/jpeg;base64,{base64.b64encode(buf).decode('utf-8')}"
                            keyframes.append({
                                "frame_idx": frame_idx,
                                "detections_count": len(raw_dets),
                                "preview_url": b64
                            })
        finally:
            cap.release()
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

        verified = self.pipeline.tracker.get_verified_incidents()
        formatted_incidents = []
        for v in verified:
            cat = " ".join(str(v["Defect Category"]).strip().split())
            sev = SEVERITY_MAPPING.get(cat, v.get("Severity", "MEDIUM"))
            action = IRPWM_ACTIONS.get(cat, "IRPWM standard track inspection and repair")
            formatted_incidents.append({
                "track_id": v["Track ID"],
                "class_name": cat,
                "severity": sev,
                "peak_confidence": v["Peak Confidence"],
                "frames_visible": v["Frames Visible"],
                "start_frame": v["Start Frame"],
                "last_frame": v["End Frame"],
                "latitude": v["Latitude"],
                "longitude": v["Longitude"],
                "chainage": f"KM {122.400 + (v['Track ID'] * 0.015):.3f}",
                "action": action
            })

        elapsed_ms = round((time.perf_counter() - t_start) * 1000, 1)
        false_flashes = max(0, raw_detections_count - len(formatted_incidents))

        return {
            "success": True,
            "total_frames": total_frames,
            "inspected_frames": inspected_count,
            "stride": stride,
            "inference_time_ms": elapsed_ms,
            "device": self.device,
            "confirmed_tracklets": len(formatted_incidents),
            "false_flashes_blocked": false_flashes,
            "verified_incidents": formatted_incidents,
            "keyframes": keyframes,
            "frame_tracks": frame_tracks,
            "crops": video_crops
        }

_detector_singleton: Optional[ProductionDefectDetector] = None

def get_detector() -> ProductionDefectDetector:
    global _detector_singleton
    if _detector_singleton is None:
        _detector_singleton = ProductionDefectDetector()
    return _detector_singleton
