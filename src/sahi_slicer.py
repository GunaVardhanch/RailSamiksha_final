"""
SAHI Batched Patch Slicer Module for RailSamiksha 4K Aerial Video Ingestion
Slices high-resolution drone frames (e.g., 3840x2160 or 2752x1536) into overlapping
tiles (e.g., 640x640 with 20% overlap) to prevent sub-pixel resolution loss on small defects.
"""

from typing import List, Tuple, Generator, Optional
import numpy as np
import cv2

class SAHISlicer:
    """
    High-throughput frame slicer implementing Slicing Aided Hyper Inference (SAHI)
    grid partitioning with configurable tile dimensions and overlap ratios.
    """

    def __init__(
        self,
        slice_height: int = 640,
        slice_width: int = 640,
        overlap_height_ratio: float = 0.20,
        overlap_width_ratio: float = 0.20,
    ):
        self.slice_height = int(slice_height)
        self.slice_width = int(slice_width)
        self.overlap_height_ratio = float(overlap_height_ratio)
        self.overlap_width_ratio = float(overlap_width_ratio)

        if not (0.0 <= self.overlap_height_ratio < 1.0 and 0.0 <= self.overlap_width_ratio < 1.0):
            raise ValueError("Overlap ratios must be in the range [0.0, 1.0).")

    def calculate_slice_bboxes(self, image_height: int, image_width: int) -> List[Tuple[int, int, int, int]]:
        """
        Calculates top-left and bottom-right pixel coordinates [x1, y1, x2, y2]
        for each tile in the overlapping grid. Ensures complete coverage to boundaries.
        """
        step_x = max(1, int(self.slice_width * (1.0 - self.overlap_width_ratio)))
        step_y = max(1, int(self.slice_height * (1.0 - self.overlap_height_ratio)))

        x_coords = list(range(0, max(1, image_width - self.slice_width + 1), step_x))
        if not x_coords or (x_coords[-1] + self.slice_width < image_width):
            x_coords.append(max(0, image_width - self.slice_width))

        y_coords = list(range(0, max(1, image_height - self.slice_height + 1), step_y))
        if not y_coords or (y_coords[-1] + self.slice_height < image_height):
            y_coords.append(max(0, image_height - self.slice_height))

        # Deduplicate coordinates in case of boundary matches
        x_coords = sorted(list(set(x_coords)))
        y_coords = sorted(list(set(y_coords)))

        slices: List[Tuple[int, int, int, int]] = []
        for y in y_coords:
            for x in x_coords:
                x2 = min(image_width, x + self.slice_width)
                y2 = min(image_height, y + self.slice_height)
                # If image is smaller than tile dimensions, clamp x1, y1
                x1 = max(0, x2 - self.slice_width)
                y1 = max(0, y2 - self.slice_height)
                slices.append((x1, y1, x2, y2))

        return slices

    def slice_image(
        self, image: np.ndarray
    ) -> Tuple[List[np.ndarray], List[Tuple[int, int, int, int]]]:
        """
        Slices a given image into tile arrays alongside their global coordinate boxes.
        
        Args:
            image: HxWxC uint8 numpy array (BGR or RGB)
        Returns:
            tiles: List of cropped tile numpy arrays of shape (slice_height, slice_width, C)
            slice_boxes: List of (x1, y1, x2, y2) global bounding boxes
        """
        h, w = image.shape[:2]
        slice_bboxes = self.calculate_slice_bboxes(h, w)
        tiles: List[np.ndarray] = []

        for x1, y1, x2, y2 in slice_bboxes:
            tile = image[y1:y2, x1:x2]
            # Handle potential edge cases where tile is smaller than target
            if tile.shape[0] != self.slice_height or tile.shape[1] != self.slice_width:
                tile = cv2.resize(tile, (self.slice_width, self.slice_height), interpolation=cv2.INTER_LINEAR)
            tiles.append(tile)

        return tiles, slice_bboxes

    def batch_slices(
        self,
        tiles: List[np.ndarray],
        slice_boxes: List[Tuple[int, int, int, int]],
        batch_size: int = 8,
    ) -> Generator[Tuple[np.ndarray, List[Tuple[int, int, int, int]]], None, None]:
        """
        Batches sliced patches for GPU VRAM batch inference.
        
        Yields:
            batch_array: (B, H, W, C) numpy array
            batch_boxes: List of corresponding (x1, y1, x2, y2) global positions
        """
        n = len(tiles)
        for i in range(0, n, batch_size):
            batch_tiles = tiles[i : i + batch_size]
            batch_boxes = slice_boxes[i : i + batch_size]
            yield np.stack(batch_tiles, axis=0), batch_boxes
