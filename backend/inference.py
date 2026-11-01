"""
RailSamiksha AI — Real-Time Aerial Defect Inference Engine
===========================================================
High-precision detection using RT-DETR-L trained on Indian Railways defect dataset.
Features:
  - GPU / CUDA accelerated inference (with CPU fallback)
  - 9 Canonical Defect Classes
  - Indian Railways P-Way Severity Classification
  - Bounding Box Normalization & Pixel Coordinates
  - OpenCV Annotation & Base64 Image Preview Generation
"""

import io
import os
import time
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional

import cv2
import numpy as np
import torch
from ultralytics import RTDETR

ROOT_DIR = Path(__file__).resolve().parent.parent
WEIGHTS_PATH = ROOT_DIR / "release_weights" / "rtdetr_v3_sanitized_85_best.pt"

# Fallback weights if primary is missing
if not WEIGHTS_PATH.exists():
    WEIGHTS_PATH = ROOT_DIR / "RailSamiksha_Production_App" / "weights" / "best.pt"

# Indian Railways P-Way Manual (IRPWM) Standards Mapping
IRPWM_STANDARDS = {
    "Rail Crack": {
        "severity": "CRITICAL",
        "action": "IRPWM Para 268: Emergency fishplate clamping & 20 kmph stop order",
        "color_bgr": (68, 68, 239)   # Red
    },
    "Rail Misalignment": {
        "severity": "CRITICAL",
        "action": "IRPWM Para 224: Immediate track slew realignment & speed restriction",
        "color_bgr": (38, 38, 220)   # Dark Red
    },
    "Rail Joint Damage": {
        "severity": "HIGH",
        "action": "IRPWM Para 241: Re-torque fishplate bolts to 650 Nm or weld joint",
        "color_bgr": (94, 63, 244)   # Rose / Orange-Red
    },
    "Missing Fastener": {
        "severity": "HIGH",
        "action": "IRPWM Para 257: Install standard ERC clip & rubber pad within 24h",
        "color_bgr": (22, 115, 249)  # Orange
    },
    "Damaged Fastener": {
        "severity": "MEDIUM",
        "action": "IRPWM Para 257: Replace Pandrol e-clip with RDSO approved MK-III",
        "color_bgr": (8, 179, 234)   # Gold / Amber
    },
    "Sleeper Defect": {
        "severity": "MEDIUM",
        "action": "IRPWM Para 234: Mark for spot PSC sleeper replacement in next block",
        "color_bgr": (246, 130, 59)  # Blue
    },
    "Foreign Objects": {
        "severity": "MEDIUM",
        "action": "IRPWM Para 219: Immediate manual track clearance of obstructions",
        "color_bgr": (247, 85, 168)  # Purple
    },
    "Rail Wear": {
        "severity": "LOW",
        "action": "IRPWM Para 302: Lubricate rail gauge face & profile grind",
        "color_bgr": (129, 185, 16)  # Emerald
    },
    "Ballast Defect": {
        "severity": "LOW",
        "action": "IRPWM Para 228: Replenish 250mm ballast cushion & tamp",
        "color_bgr": (212, 182, 6)   # Cyan
    }
}

class DefectDetector:
    def __init__(self, weights_path: Path = WEIGHTS_PATH):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"[Inference] Initializing RT-DETR-L detector on device: {self.device}")
        print(f"[Inference] Loading model weights from: {weights_path}")
        
        self.model = RTDETR(str(weights_path))
        self.names = self.model.names
        print(f"[Inference] Model loaded successfully. Class count: {len(self.names)}")

    def predict_image(
        self,
        image_bytes: bytes,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        imgsz: int = 640
    ) -> Dict[str, Any]:
        """Runs RT-DETR-L defect detection on raw image bytes."""
        t_start = time.perf_counter()

        # Decode image
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise ValueError("Could not decode image from provided bytes.")

        h_orig, w_orig = img_bgr.shape[:2]

        # Run inference
        results = self.model.predict(
            img_bgr,
            conf=conf_threshold,
            iou=iou_threshold,
            imgsz=imgsz,
            device=self.device,
            verbose=False
        )

        detections: List[Dict[str, Any]] = []
        counts_by_severity = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        annotated_img = img_bgr.copy()

        for r in results:
            boxes = r.boxes
            for idx, box in enumerate(boxes):
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                xyxy = [float(val) for val in box.xyxy[0].tolist()]

                x1, y1, x2, y2 = xyxy
                class_name = self.names.get(cls_id, f"Defect_{cls_id}")

                standard = IRPWM_STANDARDS.get(class_name, {
                    "severity": "MEDIUM",
                    "action": "IRPWM General Standard: Inspect on-site and report",
                    "color_bgr": (0, 255, 255)
                })

                severity = standard["severity"]
                counts_by_severity[severity] += 1

                # Normalized coordinates (0.0 - 1.0) for responsive canvas overlay
                norm_box = [
                    round(max(0.0, min(1.0, x1 / w_orig)), 4),
                    round(max(0.0, min(1.0, y1 / h_orig)), 4),
                    round(max(0.0, min(1.0, x2 / w_orig)), 4),
                    round(max(0.0, min(1.0, y2 / h_orig)), 4),
                ]

                # Chainage and track side heuristics
                chainage_km = 44.200 + (idx * 0.150)
                chainage_str = f"KM {chainage_km:.3f}"
                center_x = (x1 + x2) / 2
                track_side = "LEFT_RAIL" if center_x < w_orig * 0.4 else "RIGHT_RAIL" if center_x > w_orig * 0.6 else "CENTRAL_BALLAST"

                defect_record = {
                    "id": f"AI-DEF-{idx + 1:03d}",
                    "name": class_name,
                    "class_id": cls_id,
                    "confidence": round(conf, 3),
                    "confidence_pct": f"{conf:.1%}",
                    "severity": severity,
                    "action": standard["action"],
                    "chainage": chainage_str,
                    "track_side": track_side,
                    "bbox_pixels": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                    "bbox_norm": norm_box,
                    "cleared": False
                }
                detections.append(defect_record)

                # Draw bounding box on annotated preview
                color = standard["color_bgr"]
                cv2.rectangle(annotated_img, (int(x1), int(y1)), (int(x2), int(y2)), color, 3)

                label_text = f"{class_name} {conf:.0%} [{severity}]"
                (tw, th), baseline = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(annotated_img, (int(x1), max(0, int(y1) - th - 8)), (int(x1) + tw + 6, int(y1)), color, -1)
                cv2.putText(annotated_img, label_text, (int(x1) + 3, max(th, int(y1) - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        inference_ms = round((time.perf_counter() - t_start) * 1000, 1)

        # Encode annotated image to JPEG base64 for direct browser rendering
        encode_success, buffer = cv2.imencode(".jpg", annotated_img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        annotated_base64 = None
        if encode_success:
            annotated_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"

        return {
            "success": True,
            "inference_time_ms": inference_ms,
            "device": self.device,
            "image_dimensions": {"width": w_orig, "height": h_orig},
            "total_defects": len(detections),
            "severity_summary": counts_by_severity,
            "detections": detections,
            "annotated_preview_url": annotated_base64
        }

# Global singleton detector instance
_detector_instance: Optional[DefectDetector] = None

def get_detector() -> DefectDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = DefectDetector()
    return _detector_instance
