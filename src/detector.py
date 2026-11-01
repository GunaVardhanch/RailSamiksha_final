"""
RT-DETR Inference Engine for RailSamiksha 4K Aerial Track Defect Detection
Wraps Ultralytics RT-DETR models for high-throughput PyTorch and TensorRT execution.
NMS Characteristic: RT-DETR utilizes Hungarian bipartite matching and is natively NMS-free
within patches. Intra-patch NMS is bypassed.
"""

from typing import List, Dict, Any, Union, Optional
from pathlib import Path
import numpy as np
import torch
from ultralytics import RTDETR

class RTDETRDetector:
    """
    Inference engine for RT-DETR models (rtdetr-l / rtdetr-x) supporting
    batched slice inputs and native GPU execution.
    """

    def __init__(
        self,
        weights_path: Union[str, Path] = "models/rtdetr-l.pt",
        device: str = "cuda:0",
        conf_threshold: float = 0.25,
        imgsz: int = 640,
    ):
        self.weights_path = Path(weights_path)
        self.device = device if torch.cuda.is_available() and "cuda" in device else "cpu"
        self.conf_threshold = conf_threshold
        self.imgsz = imgsz

        print(f"[RTDETRDetector] Initializing model from {self.weights_path} on {self.device}...")
        self.model = RTDETR(str(self.weights_path))

    def predict_patches(
        self,
        patches_batch: np.ndarray,
        conf_threshold: Optional[float] = None,
    ) -> List[List[Dict[str, Any]]]:
        """
        Runs batched inference on sliced image tiles.
        
        Args:
            patches_batch: Array of shape (B, H, W, C) in BGR or RGB format.
            conf_threshold: Optional override for detection confidence.
            
        Returns:
            List of length B, where each element is a list of detections:
            [
                {
                    "box": [x1, y1, x2, y2], # float coordinates relative to tile
                    "score": float,
                    "class_id": int
                },
                ...
            ]
        """
        conf = conf_threshold if conf_threshold is not None else self.conf_threshold

        # Ultralytics expects a list of (H, W, C) images for batching
        if isinstance(patches_batch, np.ndarray) and patches_batch.ndim == 4:
            source = [p for p in patches_batch]
        else:
            source = patches_batch

        # Pass batch directly into model. RT-DETR does not require intra-patch NMS.
        results = self.model.predict(
            source=source,
            conf=conf,
            device=self.device,
            imgsz=self.imgsz,
            verbose=False,
        )

        batch_detections: List[List[Dict[str, Any]]] = []
        for res in results:
            patch_dets: List[Dict[str, Any]] = []
            if res.boxes is not None and len(res.boxes) > 0:
                xyxy = res.boxes.xyxy.cpu().numpy()
                confs = res.boxes.conf.cpu().numpy()
                classes = res.boxes.cls.cpu().numpy().astype(int)

                for box, score, cid in zip(xyxy, confs, classes):
                    patch_dets.append({
                        "box": [float(b) for b in box],
                        "score": float(score),
                        "class_id": int(cid),
                    })
            batch_detections.append(patch_dets)

        return batch_detections

    def predict_frame(
        self,
        frame: np.ndarray,
        conf_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Runs standard full-frame prediction (e.g. for macro-scale anomalies like ballast defect).
        """
        conf = conf_threshold if conf_threshold is not None else self.conf_threshold
        results = self.model.predict(
            source=frame,
            conf=conf,
            device=self.device,
            imgsz=self.imgsz,
            verbose=False,
        )

        frame_dets: List[Dict[str, Any]] = []
        if len(results) > 0 and results[0].boxes is not None:
            res = results[0]
            xyxy = res.boxes.xyxy.cpu().numpy()
            confs = res.boxes.conf.cpu().numpy()
            classes = res.boxes.cls.cpu().numpy().astype(int)

            for box, score, cid in zip(xyxy, confs, classes):
                frame_dets.append({
                    "box": [float(b) for b in box],
                    "score": float(score),
                    "class_id": int(cid),
                })

        return frame_dets
