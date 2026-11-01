"""
Non-Maximum Merging (NMM) Postprocessor
=======================================
Stitches detections across overlapping tile boundaries using Non-Maximum Merging
with confidence-weighted coordinate averaging, avoiding truncated defect duplicates.
"""

from typing import List, Dict, Any
import numpy as np


def compute_iou(box1: List[float], box2: List[float]) -> float:
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_w = max(0.0, x2 - x1)
    inter_h = max(0.0, y2 - y1)
    inter_area = inter_w * inter_h

    area1 = max(0.0, (box1[2] - box1[0]) * (box1[3] - box1[1]))
    area2 = max(0.0, (box2[2] - box2[0]) * (box2[3] - box2[1]))
    union_area = area1 + area2 - inter_area

    if union_area <= 0.0:
        return 0.0
    return inter_area / union_area


class NonMaximumMerger:
    def __init__(self, match_threshold: float = 0.45):
        self.match_threshold = match_threshold

    def merge_detections(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merges redundant detections belonging to the same class across tile boundaries.
        Applies confidence-weighted coordinate averaging.
        """
        if not detections:
            return []

        # Sort descending by confidence score
        sorted_dets = sorted(detections, key=lambda d: d["score"], reverse=True)
        merged_results: List[Dict[str, Any]] = []

        while sorted_dets:
            primary = sorted_dets.pop(0)
            primary_box = primary["box"]
            primary_cid = primary["class_id"]

            cluster = [primary]
            remaining = []

            for candidate in sorted_dets:
                if candidate["class_id"] == primary_cid:
                    iou = compute_iou(primary_box, candidate["box"])
                    if iou >= self.match_threshold:
                        cluster.append(candidate)
                        continue
                remaining.append(candidate)

            sorted_dets = remaining

            # Compute confidence-weighted coordinates
            total_weight = sum(item["score"] for item in cluster)
            if total_weight > 0:
                weighted_box = [
                    sum(item["box"][0] * item["score"] for item in cluster) / total_weight,
                    sum(item["box"][1] * item["score"] for item in cluster) / total_weight,
                    sum(item["box"][2] * item["score"] for item in cluster) / total_weight,
                    sum(item["box"][3] * item["score"] for item in cluster) / total_weight,
                ]
            else:
                weighted_box = primary["box"]

            merged_entry = {
                "box": weighted_box,
                "score": max(item["score"] for item in cluster),
                "class_id": primary_cid,
                "class_name": primary["class_name"],
                "severity": primary["severity"],
                "merge_count": len(cluster)
            }
            merged_results.append(merged_entry)

        return merged_results

