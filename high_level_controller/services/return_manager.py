# services/return_manager.py
# ==========================
# Return-To-Home (RTH) state machine.
# Reverses recorded path waypoints and navigates robot back to home position.
#
# Strategy:
#   1. Pop next target from reversed waypoint list
#   2. Compute heading error to target waypoint
#   3. If heading error > tolerance: issue turn command
#   4. If heading aligned: issue forward command
#   5. When within tolerance of target: pop next waypoint
#   6. When no more waypoints: declare HOME REACHED
#
# GPS mode: uses haversine distance + GPS bearing
# Local mode: uses local (x,y) coordinate difference

import asyncio
import math
import time
import threading
from typing import List, Optional, Callable

import config
from services.path_logger import Waypoint, haversine_dist, gps_bearing
from utils.logger import get_logger

log = get_logger("return_manager")


def _local_bearing(from_x: float, from_y: float, to_x: float, to_y: float) -> float:
    """Bearing in degrees from local frame, where +Y is North."""
    dx = to_x - from_x
    dy = to_y - from_y
    bearing = math.degrees(math.atan2(dx, dy))
    return (bearing + 360) % 360


def _heading_error(current_heading: float, target_bearing: float) -> float:
    """Signed heading error in degrees [-180, 180]."""
    err = target_bearing - current_heading
    while err > 180:
        err -= 360
    while err < -180:
        err += 360
    return err


class ReturnManager:
    """
    Manages return-to-home traversal.
    Should be run as an async loop by the autonomous_controller.
    """

    def __init__(self, send_cmd_fn: Callable[[str], None]):
        self._send_cmd = send_cmd_fn
        self._waypoints: List[Waypoint] = []
        self._target_idx = 0
        self._active = False
        self._home_reached = False
        self._current_x = 0.0
        self._current_y = 0.0
        self._lock = threading.Lock()

    def start(
        self,
        reverse_path: List[Waypoint],
        current_x: float, current_y: float,
        current_lat: float, current_lon: float,
    ):
        """Begin RTH with reversed waypoint list."""
        with self._lock:
            self._waypoints = [wp for wp in reverse_path if wp is not None]
            self._target_idx = 0
            self._active = True
            self._home_reached = False
            self._current_x = current_x
            self._current_y = current_y
        log.info(f"RTH started with {len(self._waypoints)} waypoints")

    def stop(self):
        with self._lock:
            self._active = False
        self._send_cmd("STOP")
        log.info("RTH stopped")

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def home_reached(self) -> bool:
        return self._home_reached

    def step(
        self,
        current_lat: float, current_lon: float, gps_ok: bool,
        current_x: float, current_y: float,
        current_heading: float
    ) -> bool:
        """
        Execute one RTH step. Call at regular intervals.
        Returns True if home has been reached.
        """
        with self._lock:
            if not self._active:
                return False
            if self._target_idx >= len(self._waypoints):
                self._declare_home_reached()
                return True

            target = self._waypoints[self._target_idx]

        # ── Compute distance and bearing to target ────────────────────────
        use_gps = gps_ok and target.gps_ok and current_lat != 0 and current_lon != 0

        if use_gps:
            dist = haversine_dist(current_lat, current_lon, target.lat, target.lon)
            bearing = gps_bearing(current_lat, current_lon, target.lat, target.lon)
            tolerance = config.RTH_WAYPOINT_TOLERANCE_GPS
        else:
            dx = target.local_x - current_x
            dy = target.local_y - current_y
            dist = math.sqrt(dx * dx + dy * dy)
            bearing = _local_bearing(current_x, current_y, target.local_x, target.local_y)
            tolerance = config.RTH_WAYPOINT_TOLERANCE_LOCAL

        log.debug(
            f"RTH step: target[{self._target_idx}] dist={dist:.2f}m "
            f"bearing={bearing:.1f}° heading={current_heading:.1f}°"
        )

        # ── Waypoint reached? ─────────────────────────────────────────────
        if dist < tolerance:
            log.info(f"Waypoint {self._target_idx} reached (dist={dist:.2f}m)")
            with self._lock:
                self._target_idx += 1
            self._send_cmd("STOP")
            return False

        # ── Heading alignment ─────────────────────────────────────────────
        heading_err = _heading_error(current_heading, bearing)

        if abs(heading_err) > config.RTH_HEADING_TOLERANCE:
            # Turn to align heading
            if heading_err > 0:
                self._send_cmd(f"RIGHT {config.RTH_TURN_SPEED}")
            else:
                self._send_cmd(f"LEFT {config.RTH_TURN_SPEED}")
        else:
            # Heading OK — move forward
            self._send_cmd(f"FORWARD {config.RTH_MOVE_SPEED}")

        return False

    def _declare_home_reached(self):
        self._active = False
        self._home_reached = True
        self._send_cmd("STOP")
        log.info("🏠 HOME REACHED — RTH complete")
