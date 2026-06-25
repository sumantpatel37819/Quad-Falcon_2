# fusion/visual_odometry_orb.py
# ==============================
# ORB-based visual odometry helper.
# Estimates relative motion between consecutive frames using:
#   - ORB feature detection
#   - BFMatcher with Lowe's ratio test
#   - Homography / essential matrix decomposition for motion cue
#
# IMPORTANT: This is a supportive motion CUES module.
# It does NOT perform metric scale estimation (not possible monocularly without
# depth information). Output is a qualitative motion vector for supplementary
# local odometry support only.
#
# ASSUMPTION: Pi camera is not calibrated — we use homography instead of
# camera intrinsics for a practical (non-metric) motion estimate.

import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple

import config
from utils.logger import get_logger

log = get_logger("visual_odometry_orb")


@dataclass
class OrbMotionEstimate:
    valid:       bool  = False
    dx_px:       float = 0.0   # Horizontal pixel shift (positive = right)
    dy_px:       float = 0.0   # Vertical pixel shift (positive = down)
    rotation_deg:float = 0.0   # Rotation estimate in degrees
    match_count: int   = 0
    confidence:  float = 0.0   # 0-1 based on inlier ratio


class VisualOdometryORB:
    """
    Tracks ORB features between consecutive frames to estimate relative motion.
    Run at lower rate than the main control loop to save CPU.
    """

    PROC_SIZE = (320, 240)  # Work at reduced resolution

    def __init__(self):
        # ORB detector
        self._orb = cv2.ORB_create(
            nfeatures=config.ORB_MAX_FEATURES,
            scaleFactor=1.2,
            nlevels=4,
        )
        self._matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

        self._prev_frame: Optional[np.ndarray] = None
        self._prev_kp    = None
        self._prev_des   = None

    def process(self, frame: np.ndarray) -> OrbMotionEstimate:
        """
        Feed a new frame; returns motion estimate relative to previous frame.
        Returns invalid estimate on first call or if tracking fails.
        """
        if frame is None or frame.size == 0:
            return OrbMotionEstimate(valid=False)

        try:
            return self._estimate(frame)
        except Exception as e:
            log.debug(f"ORB error: {e}")
            return OrbMotionEstimate(valid=False)

    def _estimate(self, frame: np.ndarray) -> OrbMotionEstimate:
        # Resize and grayscale
        small = cv2.resize(frame, self.PROC_SIZE)
        gray  = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

        kp, des = self._orb.detectAndCompute(gray, None)

        if des is None or len(kp) < 10:
            self._prev_frame = gray
            self._prev_kp = kp
            self._prev_des = des
            return OrbMotionEstimate(valid=False, match_count=len(kp) if kp else 0)

        if self._prev_des is None or len(self._prev_des) < 10:
            self._prev_frame = gray
            self._prev_kp = kp
            self._prev_des = des
            return OrbMotionEstimate(valid=False)

        # Match descriptors using kNN + Lowe's ratio test
        matches = self._matcher.knnMatch(self._prev_des, des, k=2)
        good = []
        for m_pair in matches:
            if len(m_pair) == 2:
                m, n = m_pair
                if m.distance < config.ORB_MATCH_RATIO * n.distance:
                    good.append(m)

        if len(good) < 8:
            self._prev_frame = gray
            self._prev_kp = kp
            self._prev_des = des
            return OrbMotionEstimate(valid=False, match_count=len(good))

        # Extract matched point arrays
        src_pts = np.float32([self._prev_kp[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

        # Find homography with RANSAC
        H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 3.0)
        if H is None or mask is None:
            self._prev_frame = gray
            self._prev_kp = kp
            self._prev_des = des
            return OrbMotionEstimate(valid=False, match_count=len(good))

        inlier_count = int(mask.sum())
        inlier_ratio = inlier_count / len(good)

        # Extract translation from homography (columns 0,1 translation part)
        dx = float(H[0, 2])
        dy = float(H[1, 2])

        # Extract rotation angle from homography
        angle = float(np.degrees(np.arctan2(H[1, 0], H[0, 0])))

        estimate = OrbMotionEstimate(
            valid=inlier_ratio > 0.4,
            dx_px=dx,
            dy_px=dy,
            rotation_deg=angle,
            match_count=len(good),
            confidence=inlier_ratio,
        )

        # Update previous frame
        self._prev_frame = gray
        self._prev_kp = kp
        self._prev_des = des

        log.debug(
            f"ORB: matches={len(good)}, inliers={inlier_count}, "
            f"dx={dx:.1f}px, dy={dy:.1f}px, rot={angle:.1f}°"
        )
        return estimate
