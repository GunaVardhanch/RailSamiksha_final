"""
Video & Telemetry Ingestion Engine for RailSamiksha 4K Aerial Drone Patrols
Reads video frames with high throughput and parses synchronized drone RTK-GPS/IMU .SRT metadata.
"""

import re
from pathlib import Path
from typing import Generator, Tuple, Optional, Dict, Any, List
import cv2

class TelemetryParser:
    """
    Parses drone .SRT subtitle telemetry streams (e.g., DJI Phantom / Mavic / Matrice)
    extracting latitude, longitude, altitude, and timestamp per frame.
    """

    @staticmethod
    def parse_srt(srt_path: Path) -> List[Dict[str, Any]]:
        if not srt_path.exists():
            return []

        entries = []
        with open(srt_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Regular expressions for DJI telemetry formats
        blocks = re.split(r"\n\s*\n", content.strip())
        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if len(lines) < 2:
                continue

            # Time range: 00:00:00,000 --> 00:00:00,033
            time_match = re.search(r"(\d{2}:\d{2}:\d{2}[,\.]\d{3})", lines[1] if len(lines) > 1 else lines[0])
            time_str = time_match.group(1) if time_match else ""

            # Coordinates
            text = " ".join(lines)
            lat_m = re.search(r"(?:latitude|lat)[:\s]+([+-]?\d+\.\d+)", text, re.IGNORECASE)
            lon_m = re.search(r"(?:longtitude|longitude|lon)[:\s]+([+-]?\d+\.\d+)", text, re.IGNORECASE)
            alt_m = re.search(r"(?:rel_alt|altitude|alt)[:\s]+([+-]?\d+\.\d+)", text, re.IGNORECASE)

            lat = float(lat_m.group(1)) if lat_m else None
            lon = float(lon_m.group(1)) if lon_m else None
            alt = float(alt_m.group(1)) if alt_m else None

            entries.append({
                "time_str": time_str,
                "latitude": lat,
                "longitude": lon,
                "altitude": alt,
            })

        return entries

class VideoIngestionEngine:
    """
    High-throughput video reader extracting 4K aerial frames and synchronizing telemetry.
    """

    def __init__(self, video_path: str, srt_path: Optional[str] = None):
        self.video_path = Path(video_path)
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {self.video_path}")

        self.cap = cv2.VideoCapture(str(self.video_path))
        if not self.cap.isOpened():
            raise RuntimeError(f"Unable to open video: {self.video_path}")

        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Check for matching SRT telemetry file
        actual_srt = Path(srt_path) if srt_path else self.video_path.with_suffix(".SRT")
        if not actual_srt.exists():
            actual_srt = self.video_path.with_suffix(".srt")

        self.telemetry_entries = TelemetryParser.parse_srt(actual_srt) if actual_srt.exists() else []

    def stream_frames(
        self, stride: int = 1
    ) -> Generator[Tuple[int, cv2.typing.MatLike, Dict[str, Any]], None, None]:
        """
        Streams frames sequentially with synchronized telemetry metadata.
        
        Yields:
            frame_idx: Integer index of the current frame
            frame: HxWxC BGR image
            telemetry: Dict with GPS coordinates and timestamps
        """
        frame_idx = 0
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            if frame_idx % stride == 0:
                tel = {}
                if self.telemetry_entries:
                    idx = min(frame_idx, len(self.telemetry_entries) - 1)
                    tel = self.telemetry_entries[idx]

                yield frame_idx, frame, tel

            frame_idx += 1

    def release(self):
        if self.cap.isOpened():
            self.cap.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
