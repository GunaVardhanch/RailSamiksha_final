"""
Drone Flight Telemetry Parser & Simulator
=========================================
Parses real DJI .SRT metadata (GPS coordinates, altitude, barometric barometer)
or generates synchronized flight telemetry along realistic railway corridors.
"""

from typing import Dict, Any, List
import re
import numpy as np


class TelemetrySimulator:
    def __init__(
        self,
        base_lat: float = 28.6139,
        base_lon: float = 77.2090,
        base_alt: float = 4.0,
        speed_mps: float = 1.8  # ~6.5 km/h drone survey speed
    ):
        self.base_lat = base_lat
        self.base_lon = base_lon
        self.base_alt = base_alt
        self.speed_mps = speed_mps

    def get_frame_telemetry(self, frame_idx: int, fps: float = 30.0) -> Dict[str, Any]:
        """
        Generates simulated high-precision RTK-GPS telemetry moving forward along track.
        """
        time_sec = frame_idx / max(fps, 1.0)
        dist_m = self.speed_mps * time_sec

        # Approximate 1 degree latitude = 111,000 meters
        d_lat = dist_m / 111000.0
        # Small realistic track yaw drift
        d_lon = (dist_m * 0.05) / 111000.0

        current_lat = self.base_lat + d_lat
        current_lon = self.base_lon + d_lon
        current_alt = self.base_alt + np.sin(frame_idx * 0.05) * 0.1

        return {
            "latitude": float(current_lat),
            "longitude": float(current_lon),
            "altitude": float(current_alt),
            "flight_time_sec": float(time_sec),
            "drone_speed_kmh": float(self.speed_mps * 3.6),
        }


def parse_dji_srt(srt_content: str) -> List[Dict[str, Any]]:
    """
    Parses DJI drone .SRT flight subtitle log into frame-by-frame telemetry records.
    """
    entries = []
    blocks = srt_content.strip().split("\n\n")

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        meta_line = lines[-1]
        lat_match = re.search(r"\[latitude:\s*([\d\.-]+)\]", meta_line)
        lon_match = re.search(r"\[longitude:\s*([\d\.-]+)\]", meta_line)
        alt_match = re.search(r"\[rel_alt:\s*([\d\.-]+)", meta_line)

        lat = float(lat_match.group(1)) if lat_match else 28.6139
        lon = float(lon_match.group(1)) if lon_match else 77.2090
        alt = float(alt_match.group(1)) if alt_match else 4.0

        entries.append({
            "latitude": lat,
            "longitude": lon,
            "altitude": alt,
        })

    return entries

