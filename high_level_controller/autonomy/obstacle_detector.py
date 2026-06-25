# autonomy/obstacle_detector.py
# ==============================
# Lightweight camera-based obstacle/free-space detection for Raspberry Pi 3B.
#
# Algorithm (optimised for Pi 3B CPU):
#   1. Resize frame to 320x240
#   2. Crop bottom 40% (the relevant near-ground region)
#   3. Convert to grayscale → Canny edges
#   4. Divide into Left / Center / Right thirds
#   5. Compute "obstacle density" as edge pixel fraction per sector
#   6. Invert to get free-space score (1.0 = fully free, 0.0 = fully blocked)
#
# Returns: ObstacleReport with per-sector scores

from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

import config
from utils.logger import get_logger

log = get_logger("obstacle_detector")


@dataclass
class ObstacleReport:
    left_score:   float = 1.0   # 1.0 = free, 0.0 = blocked
    center_score: float = 1.0
    right_score:  float = 1.0
    raw_frame:    Optional[np.ndarray] = None  # Debug annotated frame
    valid:        bool = False


class ObstacleDetector:
    """
    Processes camera frames to produce per-sector free-space scores.
    Optimised for Raspberry Pi 3B (no GPU, single core).
    """

    PROC_WIDTH  = 320
    PROC_HEIGHT = 240
    ROI_TOP_FRAC = 0.45   # Use bottom 55% of frame (near-ground region)

    def __init__(self):
        self._canny_low  = 40
        self._canny_high = 100

    def analyze(self, frame: np.ndarray) -> ObstacleReport:
        if frame is None or frame.size == 0:
            return ObstacleReport(valid=False)

        try:
            return self._process(frame)
        except Exception as e:
            log.error(f"Obstacle detection error: {e}")
            return ObstacleReport(valid=False)

    def _process(self, frame: np.ndarray) -> ObstacleReport:
        # 1. Resize to processing resolution
        small = cv2.resize(frame, (self.PROC_WIDTH, self.PROC_HEIGHT))

        # 2. Crop ROI (bottom region — where obstacles and floor are visible)
        roi_top = int(self.PROC_HEIGHT * self.ROI_TOP_FRAC)
        roi = small[roi_top:, :]  # Shape: (H-roi_top) x W

        # 3. Grayscale + Gaussian blur to reduce noise
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 4. Canny edge detection
        edges = cv2.Canny(blurred, self._canny_low, self._canny_high)

        # 5. Divide into thirds
        h, w = edges.shape
        left_roi   = edges[:, :w // 3]
        center_roi = edges[:, w // 3: 2 * w // 3]
        right_roi  = edges[:, 2 * w // 3:]

        def obstacle_score(region: np.ndarray) -> float:
            """Returns fraction of pixels that are edges (obstacle density)."""
            if region.size == 0:
                return 0.0
            density = np.count_nonzero(region) / region.size
            return float(density)

        left_density   = obstacle_score(left_roi)
        center_density = obstacle_score(center_roi)
        right_density  = obstacle_score(right_roi)

        # Clamp density to [0, 1] and convert to free-space score
        def to_free(density: float) -> float:
            return max(0.0, min(1.0, 1.0 - density * 8))  # ×8 amplifier

        report = ObstacleReport(
            left_score=to_free(left_density),
            center_score=to_free(center_density),
            right_score=to_free(right_density),
            valid=True,
        )

        return report
