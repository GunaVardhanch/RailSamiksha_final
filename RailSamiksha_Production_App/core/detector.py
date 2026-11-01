"""
RailSamiksha Deep Detection Engine (RT-DETR-L)
==============================================
Encapsulates fine-tuned RT-DETR-L model inference with automatic CUDA/CPU
acceleration and support for both PyTorch (.pt) and ONNX (.onnx) graphs.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import cv2
import torch
from ultralytics import RTDETR
from config import CLASS_NAMES, SEVERITY_MAPPING, SEVERITY_COLORS, CLASS_COLORS, DEFAULT_CONF


class RTDETRDetector:
    def __init__(
        self,
        weights_path: str,
        conf_threshold: float = DEFAULT_CONF,
        device: Optional[str] = None
    ):
        self.weights_path = weights_path
        self.conf_threshold = conf_threshold

        if device is None:
            self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.model = RTDETR(self.weights_path)
        self.names = getattr(self.model, "names", CLASS_NAMES)

    def detect_single(
        self,
        image: np.ndarray,
        imgsz: int = 640
    ) -> List[Dict[str, Any]]:
        """
        Runs detection on a single image/tile.
        Returns list of detections with box [x1, y1, x2, y2], conf, class_id, class_name, severity.
        """
        results = self.model.predict(
            source=image,
            conf=self.conf_threshold,
            imgsz=imgsz,
            device=self.device,
            verbose=False
        )

        detections = []
        if not results:
            return detections

        res = results[0]
        boxes = res.boxes.xyxy.cpu().numpy()
        confs = res.boxes.conf.cpu().numpy()
        classes = res.boxes.cls.cpu().numpy().astype(int)

        for box, conf, cid in zip(boxes, confs, classes):
            cname = self.names.get(cid, f"Defect_{cid}")
            severity = SEVERITY_MAPPING.get(cname, "MEDIUM")
            detections.append({
                "box": box.tolist(),
                "score": float(conf),
                "class_id": int(cid),
                "class_name": cname,
                "severity": severity
            })

        return detections

    def detect_batch(
        self,
        patches: List[np.ndarray],
        imgsz: int = 640
    ) -> List[List[Dict[str, Any]]]:
        """
        Runs batched GPU detection on multiple patches.
        """
        if not patches:
            return []

        results = self.model.predict(
            source=patches,
            conf=self.conf_threshold,
            imgsz=imgsz,
            device=self.device,
            verbose=False
        )

        batch_detections = []
        for res in results:
            dets = []
            boxes = res.boxes.xyxy.cpu().numpy()
            confs = res.boxes.conf.cpu().numpy()
            classes = res.boxes.cls.cpu().numpy().astype(int)

            for box, conf, cid in zip(boxes, confs, classes):
                cname = self.names.get(cid, f"Defect_{cid}")
                severity = SEVERITY_MAPPING.get(cname, "MEDIUM")
                dets.append({
                    "box": box.tolist(),
                    "score": float(conf),
                    "class_id": int(cid),
                    "class_name": cname,
                    "severity": severity
                })
            batch_detections.append(dets)

        return batch_detections


def annotate_detections(
    image: np.ndarray,
    detections: List[Dict[str, Any]],
    line_thickness: int = 3,
    font_scale: float = 0.75
) -> np.ndarray:
    """
    Renders high-contrast bounding boxes, severity badges, and class confidence tags.
    """
    canvas = image.copy()
    h, w = canvas.shape[:2]

    for det in detections:
        box = [int(round(c)) for c in det["box"]]
        x1, y1, x2, y2 = box
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w - 1, x2), min(h - 1, y2)

        cid = det.get("class_id", 0)
        cname = det.get("class_name", "Defect")
        conf = det.get("score", 0.0)
        severity = det.get("severity", "MEDIUM")

        # Color based on class
        color = CLASS_COLORS.get(cid, (239, 68, 68))
        # BGR for OpenCV
        color_bgr = (color[2], color[1], color[0])

        # Draw bounding box
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color_bgr, line_thickness)

        # Label tag
        track_id = det.get("track_id", None)
        if track_id is not None:
            tag = f"#{track_id} {cname} {conf:.0%} [{severity}]"
        else:
            tag = f"{cname} {conf:.0%} [{severity}]"

        (tw, th), baseline = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)
        tag_y1 = max(0, y1 - th - baseline - 6)
        tag_y2 = y1

        cv2.rectangle(canvas, (x1, tag_y1), (x1 + tw + 10, tag_y2), color_bgr, -1)
        cv2.putText(
            canvas,
            tag,
            (x1 + 5, tag_y2 - baseline - 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

    return canvas

