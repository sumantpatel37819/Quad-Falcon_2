# autonomy/free_path_selector.py
# ================================
# Decision logic: converts per-sector obstacle scores into a motor command.
#
# Priority rules:
#   1. If center is free → FORWARD
#   2. If center blocked, left free → TURN_LEFT
#   3. If center blocked, right free → TURN_RIGHT
#   4. If all blocked → STOP_SCAN (rotates slowly in place to find path)
#
# Center bias: adds a small bonus score to center to prefer straight travel.

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import config
from autonomy.obstacle_detector import ObstacleReport
from utils.logger import get_logger

log = get_logger("free_path_selector")


class NavDecision(str, Enum):
    FORWARD   = "FORWARD"
    TURN_LEFT  = "TURN_LEFT"
    TURN_RIGHT = "TURN_RIGHT"
    STOP_SCAN  = "STOP_SCAN"
    UNKNOWN    = "UNKNOWN"


@dataclass
class NavResult:
    decision:      NavDecision = NavDecision.UNKNOWN
    left_score:    float       = 0.0
    center_score:  float       = 0.0
    right_score:   float       = 0.0
    reason:        str         = ""


class FreePathSelector:
    """
    Converts ObstacleReport into a navigation decision.
    Uses a configurable threshold to determine if a sector is "free".
    """

    def __init__(self):
        self._threshold = config.OBSTACLE_THRESHOLD
        self._center_bias = config.FORWARD_BIAS

    def decide(self, report: ObstacleReport) -> NavResult:
        if not report.valid:
            return NavResult(decision=NavDecision.UNKNOWN, reason="invalid_report")

        left   = report.left_score
        right  = report.right_score
        center = report.center_score + self._center_bias  # Bias toward forward

        is_left_free   = left   >= self._threshold
        is_center_free = center >= self._threshold
        is_right_free  = right  >= self._threshold

        result = NavResult(
            left_score=report.left_score,
            center_score=report.center_score,
            right_score=report.right_score,
        )

        if is_center_free:
            result.decision = NavDecision.FORWARD
            result.reason = f"center_free({report.center_score:.2f})"
        elif is_left_free and not is_right_free:
            result.decision = NavDecision.TURN_LEFT
            result.reason = f"center_blocked, left_free({left:.2f})"
        elif is_right_free and not is_left_free:
            result.decision = NavDecision.TURN_RIGHT
            result.reason = f"center_blocked, right_free({right:.2f})"
        elif is_left_free and is_right_free:
            # Both sides free — pick the better one
            if left >= right:
                result.decision = NavDecision.TURN_LEFT
                result.reason = f"both_free, prefer_left({left:.2f}>{right:.2f})"
            else:
                result.decision = NavDecision.TURN_RIGHT
                result.reason = f"both_free, prefer_right({right:.2f}>{left:.2f})"
        else:
            result.decision = NavDecision.STOP_SCAN
            result.reason = f"all_blocked (L={left:.2f} C={report.center_score:.2f} R={right:.2f})"

        log.debug(f"NavDecision: {result.decision.value} — {result.reason}")
        return result
