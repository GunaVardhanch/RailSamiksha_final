"""
ByteTrack-Inspired Temporal Deduplication & Defect Persistence Tracker
======================================================================
Tracks detected railway defects across sequential video frames, eliminates
flickering false alarms via multi-hit temporal confirmation, and logs incidents.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from core.merger import compute_iou


class TrackedIncident:
    def __init__(self, track_id: int, initial_detection: Dict[str, Any], frame_idx: int, telemetry: Optional[Dict[str, Any]] = None):
        self.track_id = track_id
        self.class_id = initial_detection["class_id"]
        self.class_name = initial_detection["class_name"]
        self.severity = initial_detection["severity"]
        self.box = initial_detection["box"]
        self.peak_score = initial_detection["score"]
        self.start_frame = frame_idx
        self.last_frame = frame_idx
        self.hit_count = 1
        self.miss_count = 0
        self.telemetry = telemetry or {}

    def update(self, detection: Dict[str, Any], frame_idx: int, telemetry: Optional[Dict[str, Any]] = None):
        self.box = detection["box"]
        self.peak_score = max(self.peak_score, detection["score"])
        self.last_frame = frame_idx
        self.hit_count += 1
        self.miss_count = 0
        if telemetry:
            self.telemetry = telemetry

    def mark_miss(self):
        self.miss_count += 1


class DefectTracker:
    def __init__(
        self,
        match_thresh: float = 0.35,
        min_hits: int = 3,
        max_misses: int = 5
    ):
        self.match_thresh = match_thresh
        self.min_hits = min_hits
        self.max_misses = max_misses
        self.next_track_id = 1
        self.active_tracks: List[TrackedIncident] = []
        self.all_incidents: List[TrackedIncident] = []

    def update(
        self,
        detections: List[Dict[str, Any]],
        frame_idx: int,
        telemetry: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Associates detections with existing active tracks or instantiates new tracks.
        Returns the list of detections augmented with track_id and verification status.
        """
        matched_det_indices = set()
        matched_track_indices = set()

        # Match active tracks to current detections based on class and IoU
        if self.active_tracks and detections:
            for t_idx, track in enumerate(self.active_tracks):
                best_iou = 0.0
                best_d_idx = -1
                for d_idx, det in enumerate(detections):
                    if d_idx in matched_det_indices:
                        continue
                    if det["class_id"] != track.class_id:
                        continue
                    iou = compute_iou(track.box, det["box"])
                    if iou > best_iou:
                        best_iou = iou
                        best_d_idx = d_idx

                if best_iou >= self.match_thresh and best_d_idx != -1:
                    track.update(detections[best_d_idx], frame_idx, telemetry)
                    matched_det_indices.add(best_d_idx)
                    matched_track_indices.add(t_idx)

        # Handle unmatched active tracks
        unmatched_tracks = []
        for t_idx, track in enumerate(self.active_tracks):
            if t_idx not in matched_track_indices:
                track.mark_miss()
                if track.miss_count <= self.max_misses:
                    unmatched_tracks.append(track)
            else:
                unmatched_tracks.append(track)
        self.active_tracks = unmatched_tracks

        # Instantiate new tracks for unmatched detections
        augmented_detections = []
        for d_idx, det in enumerate(detections):
            if d_idx not in matched_det_indices:
                new_track = TrackedIncident(self.next_track_id, det, frame_idx, telemetry)
                self.next_track_id += 1
                self.active_tracks.append(new_track)
                self.all_incidents.append(new_track)
                det["track_id"] = new_track.track_id
                det["is_verified"] = (new_track.hit_count >= self.min_hits)
            else:
                # Find which track matched this detection
                for track in self.active_tracks:
                    if track.box == det["box"] or (track.last_frame == frame_idx and track.class_id == det["class_id"]):
                        det["track_id"] = track.track_id
                        det["is_verified"] = (track.hit_count >= self.min_hits)
                        break

            augmented_detections.append(det)

        return augmented_detections

    def get_verified_incidents(self) -> List[Dict[str, Any]]:
        """
        Returns all incidents that passed the persistence threshold.
        """
        records = []
        for inc in self.all_incidents:
            if inc.hit_count >= self.min_hits:
                lat = inc.telemetry.get("latitude", 28.6139)
                lon = inc.telemetry.get("longitude", 77.2090)
                alt = inc.telemetry.get("altitude", 3.5)
                records.append({
                    "Track ID": inc.track_id,
                    "Defect Category": inc.class_name,
                    "Severity": inc.severity,
                    "Peak Confidence": f"{inc.peak_score:.1%}",
                    "Start Frame": inc.start_frame,
                    "End Frame": inc.last_frame,
                    "Frames Visible": inc.hit_count,
                    "Latitude": round(lat, 6),
                    "Longitude": round(lon, 6),
                    "Altitude (m)": round(alt, 1),
                })
        return records

