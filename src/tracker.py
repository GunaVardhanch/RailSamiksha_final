"""
Temporal Association & Deduplication Tracker for RailSamiksha 4K Drone Patrols
Integrates ByteTrack Kalman filtering with a temporal flicker filter (>= 3 frame hits)
to ensure a stationary defect filmed over 30+ frames triggers exactly ONE confirmed alert.
"""

from typing import List, Dict, Any, Optional
import warnings
import numpy as np
import supervision as sv

# Suppress supervision internal ByteTrack deprecation warning until v0.31 migration
warnings.filterwarnings("ignore", category=FutureWarning, module="supervision")

class DefectTracker:
    """
    ByteTrack-based temporal tracker with Kalman trajectory filtering,
    flicker filtering, and persistent defect alert deduplication.
    """

    def __init__(
        self,
        track_thresh: float = 0.25,
        match_thresh: float = 0.80,
        min_consecutive_hits: int = 3,
        lost_track_buffer: int = 30,
        frame_rate: float = 30.0,
    ):
        self.track_thresh = track_thresh
        self.match_thresh = match_thresh
        self.min_consecutive_hits = min_consecutive_hits
        self.lost_track_buffer = lost_track_buffer
        self.frame_rate = frame_rate

        # Initialize underlying ByteTrack
        self.tracker = sv.ByteTrack(
            track_activation_threshold=self.track_thresh,
            lost_track_buffer=self.lost_track_buffer,
            minimum_matching_threshold=self.match_thresh,
            frame_rate=self.frame_rate,
            minimum_consecutive_frames=self.min_consecutive_hits,
        )

        # Persistent defect ledger: track_id -> metadata
        self.confirmed_alerts: Dict[int, Dict[str, Any]] = {}
        self.track_history: Dict[int, Dict[str, Any]] = {}

    def update(
        self,
        detections: List[Dict[str, Any]],
        frame_idx: int = 0,
        telemetry: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Updates tracks with detections from current frame.
        
        Args:
            detections: List of dicts with 'box': [x1, y1, x2, y2], 'score': float, 'class_id': int
            frame_idx: Current video frame index
            telemetry: Optional dict containing GPS latitude, longitude, altitude
            
        Returns:
            List of active tracked objects with track_id and alert status.
        """
        if not detections:
            # Empty detection update
            empty_sv = sv.Detections.empty()
            self.tracker.update_with_detections(empty_sv)
            return []

        # Convert to supervision format
        xyxy = np.array([d["box"] for d in detections], dtype=np.float32)
        confidence = np.array([d["score"] for d in detections], dtype=np.float32)
        class_id = np.array([d["class_id"] for d in detections], dtype=int)

        sv_dets = sv.Detections(
            xyxy=xyxy,
            confidence=confidence,
            class_id=class_id,
        )

        tracked_sv = self.tracker.update_with_detections(sv_dets)

        tracked_results: List[Dict[str, Any]] = []

        if tracked_sv.tracker_id is not None and len(tracked_sv.tracker_id) > 0:
            for i, tid in enumerate(tracked_sv.tracker_id):
                box = [float(c) for c in tracked_sv.xyxy[i]]
                score = float(tracked_sv.confidence[i]) if tracked_sv.confidence is not None else 1.0
                cid = int(tracked_sv.class_id[i]) if tracked_sv.class_id is not None else -1

                # Update track hit history
                if tid not in self.track_history:
                    self.track_history[tid] = {
                        "track_id": int(tid),
                        "class_id": cid,
                        "first_frame": frame_idx,
                        "last_frame": frame_idx,
                        "hits": 1,
                        "best_box": box,
                        "best_score": score,
                        "telemetry": telemetry or {},
                    }
                else:
                    rec = self.track_history[tid]
                    rec["hits"] += 1
                    rec["last_frame"] = frame_idx
                    if score > rec["best_score"]:
                        rec["best_score"] = score
                        rec["best_box"] = box
                    if telemetry:
                        rec["telemetry"] = telemetry

                hist = self.track_history[tid]
                is_confirmed = hist["hits"] >= self.min_consecutive_hits

                if is_confirmed and tid not in self.confirmed_alerts:
                    # Register new confirmed defect alert
                    self.confirmed_alerts[tid] = hist

                tracked_results.append({
                    "track_id": int(tid),
                    "box": box,
                    "score": score,
                    "class_id": cid,
                    "hits": hist["hits"],
                    "is_confirmed": is_confirmed,
                })

        return tracked_results

    def get_confirmed_alerts(self) -> List[Dict[str, Any]]:
        """Returns the deduplicated list of all confirmed defect events."""
        return list(self.confirmed_alerts.values())

    def reset(self):
        """Resets tracker states between video sequences."""
        self.tracker.reset()
        self.confirmed_alerts.clear()
        self.track_history.clear()
