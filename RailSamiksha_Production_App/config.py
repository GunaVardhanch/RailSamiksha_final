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

# 9 Canonical Fine-Tuned Defect Classes (Ultralytics RT-DETR)
CLASS_NAMES = {
    0: "Ballast Deficiency",
    1: "Ballast Washout",
    2: "Broken Sleeper",
    3: "Damaged Fastener",
    4: "Missing Sleeper",
    5: "Missing Fastener",
    6: "Rail Crack",
    7: "Rail Joint Damage",
    8: "Rail Misalignment",
}

# Defect Severity Classification (Indian Railways P-Way Standard)
SEVERITY_MAPPING = {
    "Rail Crack": "CRITICAL",
    "Broken Sleeper": "CRITICAL",
    "Missing Sleeper": "CRITICAL",
    "Missing  Sleeper": "CRITICAL",
    "Rail Misalignment": "CRITICAL",
    "Rail Joint Damage": "HIGH",
    "Ballast Washout": "HIGH",
    "Missing Fastener": "HIGH",
    "Damaged Fastener": "MEDIUM",
    "Ballast Deficiency": "MEDIUM",
    # Legacy fallbacks
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
    0: (6, 182, 212),     # Ballast Deficiency - Cyan
    1: (251, 146, 60),    # Ballast Washout - Orange
    2: (244, 63, 94),     # Broken Sleeper - Crimson
    3: (234, 179, 8),     # Damaged Fastener - Gold
    4: (236, 72, 153),    # Missing Sleeper - Magenta
    5: (245, 158, 11),    # Missing Fastener - Amber
    6: (239, 68, 68),     # Rail Crack - Red (Critical)
    7: (249, 115, 22),    # Rail Joint Damage - Solar Orange
    8: (59, 130, 246),    # Rail Misalignment - Blue
}

# Defaults
DEFAULT_CONF = 0.30
DEFAULT_IOU = 0.45
DEFAULT_SLICE_SIZE = 640
DEFAULT_OVERLAP = 0.20
DEFAULT_TEMPORAL_HITS = 3
DEFAULT_VIDEO_STRIDE = 2

