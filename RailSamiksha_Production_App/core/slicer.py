"""
SAHI Patch Slicing Pipeline (1:1 Scale Preservation)
=====================================================
Slices high-resolution drone frames into native 640x640 patches with 20% overlap,
bypassing 4K-to-640 downscaling collapse and preserving microscopic defect scale.
"""

from typing import List, Tuple
import numpy as np


class SAHIPatchSlicer:
    def __init__(
        self,
        slice_height: int = 640,
        slice_width: int = 640,
        overlap_height_ratio: float = 0.20,
        overlap_width_ratio: float = 0.20
    ):
        self.slice_height = slice_height
        self.slice_width = slice_width
        self.overlap_height_ratio = overlap_height_ratio
        self.overlap_width_ratio = overlap_width_ratio

    def calculate_slice_bboxes(self, image_height: int, image_width: int) -> List[Tuple[int, int, int, int]]:
        """
        Calculates slice window boundaries (x1, y1, x2, y2) covering the image.
        """
        # If image is smaller than or equal to slice dimension, return single window
        if image_height <= self.slice_height and image_width <= self.slice_width:
            return [(0, 0, image_width, image_height)]

        stride_h = int(self.slice_height * (1.0 - self.overlap_height_ratio))
        stride_w = int(self.slice_width * (1.0 - self.overlap_width_ratio))
        stride_h = max(stride_h, 32)
        stride_w = max(stride_w, 32)

        # Vertical positions
        y_coords = list(range(0, max(1, image_height - self.slice_height + 1), stride_h))
        if not y_coords or (y_coords[-1] + self.slice_height < image_height):
            y_coords.append(max(0, image_height - self.slice_height))
        y_coords = sorted(list(set(y_coords)))

        # Horizontal positions
        x_coords = list(range(0, max(1, image_width - self.slice_width + 1), stride_w))
        if not x_coords or (x_coords[-1] + self.slice_width < image_width):
            x_coords.append(max(0, image_width - self.slice_width))
        x_coords = sorted(list(set(x_coords)))

        slice_bboxes = []
        for y in y_coords:
            for x in x_coords:
                x2 = min(image_width, x + self.slice_width)
                y2 = min(image_height, y + self.slice_height)
                slice_bboxes.append((x, y, x2, y2))

        return slice_bboxes

    def slice_image(self, image: np.ndarray) -> Tuple[List[np.ndarray], List[Tuple[int, int, int, int]]]:
        """
        Extracts cropped sub-image arrays for all slice windows.
        """
        h, w = image.shape[:2]
        slice_bboxes = self.calculate_slice_bboxes(h, w)
        patches = [image[y1:y2, x1:x2] for (x1, y1, x2, y2) in slice_bboxes]
        return patches, slice_bboxes

