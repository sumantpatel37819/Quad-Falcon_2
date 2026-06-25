# services/path_logger.py
# ========================
# Records robot waypoints during movement for path visualization and RTH.
# Waypoints are stored as a list; home pose is the first waypoint.
# Supports both GPS-based and local-coordinate tracking.

import json
import math
import time
import threading
from dataclasses import dataclass, field, asdict
from typing import List, Optional

import config
from utils.logger import get_logger

log = get_logger("path_logger")

EARTH_RADIUS_M = 6_371_000.0  # metres


@dataclass
class Waypoint:
    timestamp:  float   = field(default_factory=time.time)
    lat:        float   = 0.0      # GPS latitude (0 if GPS invalid)
    lon:        float   = 0.0      # GPS longitude (0 if GPS invalid)
    gps_ok:     bool    = False
    local_x:    float   = 0.0     # Estimated local X (east, metres)
    local_y:    float   = 0.0     # Estimated local Y (north, metres)
    yaw:        float   = 0.0     # Heading (degrees)
    mode:       str     = "MANUAL"
    cmd:        str     = "STOP"


def haversine_dist(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns distance in metres between two GPS coordinates."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return EARTH_RADIUS_M * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def gps_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial bearing from point 1 to point 2 in degrees [0, 360)."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dlam = math.radians(lon2 - lon1)
    y = math.sin(dlam) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360) % 360


class PathLogger:
    def __init__(self):
        self._waypoints: List[Waypoint] = []
        self._lock = threading.Lock()
        self._home: Optional[Waypoint] = None
        self._current: Waypoint = Waypoint()
        self._local_x = 0.0
        self._local_y = 0.0
        self._last_record_time = 0.0

    @property
    def home(self) -> Optional[Waypoint]:
        return self._home

    @property
    def waypoints(self) -> List[Waypoint]:
        with self._lock:
            return list(self._waypoints)

    def get_path_for_dashboard(self) -> list:
        """Returns waypoints as a list of dicts for the dashboard."""
        with self._lock:
            return [asdict(w) for w in self._waypoints]

    def get_reverse_path(self) -> List[Waypoint]:
        """Returns waypoints in reverse order (for return-to-home)."""
        with self._lock:
            return list(reversed(self._waypoints))

    def record(
        self,
        lat: float, lon: float, gps_ok: bool,
        yaw: float, mode: str, cmd: str,
        prev_cmd: str = "STOP", dt: float = 0.1
    ):
        """
        Record a new waypoint if the robot has moved enough.
        Also updates local (x, y) position estimate using IMU heading + motion.
        """
        # Update local pose estimate via dead reckoning
        self._update_local_pose(prev_cmd, yaw, dt)

        now = time.time()
        if now - self._last_record_time < 0.5:
            return  # Throttle to max 2 waypoints/sec

        # Compute distance from last waypoint
        with self._lock:
            if self._waypoints:
                last = self._waypoints[-1]
                if gps_ok and last.gps_ok:
                    dist = haversine_dist(last.lat, last.lon, lat, lon)
                else:
                    dx = self._local_x - last.local_x
                    dy = self._local_y - last.local_y
                    dist = math.sqrt(dx * dx + dy * dy)
            else:
                dist = config.WAYPOINT_MIN_DISTANCE + 1  # Force first record

        if dist < config.WAYPOINT_MIN_DISTANCE:
            return

        wp = Waypoint(
            timestamp=now,
            lat=lat, lon=lon, gps_ok=gps_ok,
            local_x=self._local_x, local_y=self._local_y,
            yaw=yaw, mode=mode, cmd=cmd,
        )

        with self._lock:
            if not self._waypoints:
                # First waypoint is home
                self._home = wp
                log.info(f"Home pose set: lat={lat:.6f}, lon={lon:.6f}, local=(0,0)")
            self._waypoints.append(wp)
            self._last_record_time = now

        log.debug(f"Waypoint recorded: local=({self._local_x:.2f},{self._local_y:.2f}) gps_ok={gps_ok}")

    def reset(self):
        """Clear all waypoints and reset home."""
        with self._lock:
            self._waypoints.clear()
            self._home = None
            self._local_x = 0.0
            self._local_y = 0.0
        log.info("Path logger reset")

    def save_to_disk(self):
        """Persist path to disk for crash recovery."""
        try:
            with self._lock:
                data = [asdict(w) for w in self._waypoints]
            with open(config.PATH_LOG_FILE, "w") as f:
                json.dump(data, f)
        except Exception as e:
            log.error(f"Failed to save path: {e}")

    def _update_local_pose(self, cmd: str, yaw_deg: float, dt: float):
        """
        Approximate local (x, y) update from motion command + heading.
        Uses a fixed estimated speed (metres per second) per motion command.
        ASSUMPTION: 1 motor speed unit ≈ constant velocity (simplified).
        """
        SPEED_MPS = 0.3  # Approximate robot speed in m/s when moving

        yaw_rad = math.radians(yaw_deg)
        if cmd in ("FORWARD",):
            self._local_x += SPEED_MPS * dt * math.sin(yaw_rad)
            self._local_y += SPEED_MPS * dt * math.cos(yaw_rad)
        elif cmd in ("BACKWARD",):
            self._local_x -= SPEED_MPS * dt * math.sin(yaw_rad)
            self._local_y -= SPEED_MPS * dt * math.cos(yaw_rad)
        # LEFT/RIGHT/STOP: rotation only, no translation
