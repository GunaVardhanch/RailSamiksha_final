"""
Inter-Patch Postprocessing & Coordinate Remapping Module for RailSamiksha
Re-maps patch-level coordinates to global 4K frame coordinates and reconciles
slice boundary overlaps using Non-Maximum Merging (NMM) or NMS.
"""

from typing import List, Dict, Any, Tuple
import numpy as np

def compute_iou(box_a: List[float], box_b: List[float]) -> float:
    """Computes Intersection over Union (IoU) between two [x1, y1, x2, y2] boxes."""
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])

    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area_a = max(0.0, box_a[2] - box_a[0]) * max(0.0, box_a[3] - box_a[1])
    area_b = max(0.0, box_b[2] - box_b[0]) * max(0.0, box_b[3] - box_b[1])
    union = area_a + area_b - intersection

    return intersection / (union + 1e-7)

class PostProcessor:
    """
    Handles coordinate transformation from tile coordinate spaces to 4K global canvas
    and merges boundary-fragmented detections across overlapping slices.
    """

    def __init__(self, iou_threshold: float = 0.50, merger_type: str = "nmm"):
        self.iou_threshold = float(iou_threshold)
        self.merger_type = merger_type.lower()

    @staticmethod
    def remap_to_global(
        patch_dets: List[Dict[str, Any]],
        slice_box: Tuple[int, int, int, int],
        frame_width: int,
        frame_height: int,
    ) -> List[Dict[str, Any]]:
        """
        Remaps tile-local coordinates [x1, y1, x2, y2] to global frame coordinates.
        """
        sx1, sy1, _, _ = slice_box
        remapped: List[Dict[str, Any]] = []

        for det in patch_dets:
            lx1, ly1, lx2, ly2 = det["box"]
            gx1 = max(0.0, min(float(frame_width), lx1 + sx1))
            gy1 = max(0.0, min(float(frame_height), ly1 + sy1))
            gx2 = max(0.0, min(float(frame_width), lx2 + sx1))
            gy2 = max(0.0, min(float(frame_height), ly2 + sy1))

            remapped.append({
                "box": [gx1, gy1, gx2, gy2],
                "score": float(det["score"]),
                "class_id": int(det["class_id"]),
            })

        return remapped

    def merge_detections(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Applies Non-Maximum Merging (NMM) or NMS across the aggregated global detections.
        """
        if not detections:
            return []

        if self.merger_type == "nms":
            return self._apply_nms(detections)
        else:
            return self._apply_nmm(detections)

    def _apply_nmm(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Non-Maximum Merging (NMM):
        Groups overlapping bounding boxes of the same defect class across slice boundaries
        and computes a score-weighted average of their coordinates.
        """
        # Group by class ID
        by_class: Dict[int, List[Dict[str, Any]]] = {}
        for d in detections:
            cid = d["class_id"]
            if cid not in by_class:
                by_class[cid] = []
            by_class[cid].append(d)

        merged_results: List[Dict[str, Any]] = []

        for cid, class_dets in by_class.items():
            # Sort descending by score
            sorted_dets = sorted(class_dets, key=lambda x: x["score"], reverse=True)
            used = [False] * len(sorted_dets)

            for i in range(len(sorted_dets)):
                if used[i]:
                    continue

                cluster = [sorted_dets[i]]
                used[i] = True

                for j in range(i + 1, len(sorted_dets)):
                    if not used[j]:
                        iou = compute_iou(sorted_dets[i]["box"], sorted_dets[j]["box"])
                        if iou >= self.iou_threshold:
                            cluster.append(sorted_dets[j])
                            used[j] = True

                # Weighted average merging
                total_weight = sum(c["score"] for c in cluster)
                merged_box = [0.0, 0.0, 0.0, 0.0]
                for c in cluster:
                    weight = c["score"] / (total_weight + 1e-7)
                    for k in range(4):
                        merged_box[k] += c["box"][k] * weight

                # Representative score is max score in cluster
                best_score = max(c["score"] for c in cluster)

                merged_results.append({
                    "box": merged_box,
                    "score": best_score,
                    "class_id": cid,
                    "merge_count": len(cluster),
                })

        return merged_results

    def _apply_nms(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Standard Non-Maximum Suppression (NMS)."""
        by_class: Dict[int, List[Dict[str, Any]]] = {}
        for d in detections:
            cid = d["class_id"]
            if cid not in by_class:
                by_class[cid] = []
            by_class[cid].append(d)

        kept: List[Dict[str, Any]] = []
        for cid, class_dets in by_class.items():
            sorted_dets = sorted(class_dets, key=lambda x: x["score"], reverse=True)
            while sorted_dets:
                best = sorted_dets.pop(0)
                kept.append(best)
                sorted_dets = [
                    d for d in sorted_dets
                    if compute_iou(best["box"], d["box"]) < self.iou_threshold
                ]

        return kept
