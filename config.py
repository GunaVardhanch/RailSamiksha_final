"""
RailSamiksha Production App Configuration
=========================================
Central configuration for model weights, classes, severity levels, and inference defaults.
"""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
WEIGHTS_DIR = BASE_DIR / "weights"
DEFAULT_PYTORCH_WEIGHTS = str(WEIGHTS_DIR / "best.pt")
DEFAULT_ONNX_WEIGHTS = str(WEIGHTS_DIR / "best.onnx")
SAMPLES_DIR = BASE_DIR / "samples"

# 9 Canonical Defect Classes (Trained on 2,544 images / 4,293 bboxes)
CLASS_NAMES = {
    0: "Ballast Defect",
    1: "Damaged Fastener",
    2: "Foreign Objects",
    3: "Missing Fastener",
    4: "Rail Crack",
    5: "Rail Joint Damage",
    6: "Rail Misalignment",
    7: "Rail Wear",
    8: "Sleeper Defect",
}

# Defect Severity Classification (Indian Railways P-Way Standard)
SEVERITY_MAPPING = {
    "Rail Crack": "CRITICAL",
    "Rail Misalignment": "CRITICAL",
    "Rail Joint Damage": "HIGH",
    "Missing Fastener": "HIGH",
    "Damaged Fastener": "MEDIUM",
    "Sleeper Defect": "MEDIUM",
    "Foreign Objects": "MEDIUM",
    "Rail Wear": "LOW",
    "Ballast Defect": "LOW",
}

# Distinct UI Colors (RGB tuples)
SEVERITY_COLORS = {
    "CRITICAL": (239, 68, 68),    # Laser Red
    "HIGH": (249, 115, 22),        # Solar Orange
    "MEDIUM": (234, 179, 8),       # Vivid Amber
    "LOW": (6, 182, 212),          # Cyber Cyan
}

CLASS_COLORS = {
    0: (6, 182, 212),     # Ballast Defect - Cyan
    1: (234, 179, 8),     # Damaged Fastener - Gold
    2: (168, 85, 247),    # Foreign Objects - Purple
    3: (249, 115, 22),    # Missing Fastener - Orange
    4: (239, 68, 68),     # Rail Crack - Red (Critical)
    5: (244, 63, 94),     # Rail Joint Damage - Rose
    6: (220, 38, 38),     # Rail Misalignment - Dark Red (Critical)
    7: (16, 185, 129),    # Rail Wear - Emerald
    8: (59, 130, 246),    # Sleeper Defect - Blue
}

# Defaults
DEFAULT_CONF = 0.30
DEFAULT_IOU = 0.45
DEFAULT_SLICE_SIZE = 640
DEFAULT_OVERLAP = 0.20
DEFAULT_TEMPORAL_HITS = 3
DEFAULT_VIDEO_STRIDE = 2

