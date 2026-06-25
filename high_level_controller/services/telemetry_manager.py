# services/telemetry_manager.py
# ==============================
# Parses raw Arduino telemetry dicts and maintains current robot telemetry state.
# Also manages the dashboard keepalive / command timeout watchdog.

import time
import threading
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable

import config
from utils.logger import get_logger

log = get_logger("telemetry_manager")


@dataclass
class TelemetryState:
    # IMU
    yaw:   float = 0.0
    pitch: float = 0.0
    roll:  float = 0.0

    # GPS
    lat:      float = 0.0
    lon:      float = 0.0
    gps_ok:   bool  = False
    sats:     int   = 0
    gps_spd:  float = 0.0

    # Motor
    spd:  int  = 0
    cmd:  str  = "STOP"

    # Safety
    estop: bool = False

    # Arduino uptime
    arduino_t_ms: int = 0

    # Pi-side bookkeeping
    arduino_connected: bool = False
    last_update_ts:    float = field(default_factory=time.time)


class TelemetryManager:
    """
    Thread-safe store for the latest robot telemetry.
    Calls optional callbacks when new data arrives.
    """

    def __init__(self):
        self._state = TelemetryState()
        self._lock = threading.Lock()
        self._on_update: Optional[Callable[[dict], None]] = None

        # Dashboard keepalive watchdog
        self._last_dashboard_ping = time.time()
        self._watchdog_thread: Optional[threading.Thread] = None
        self._watchdog_running = False
        self._estop_callback: Optional[Callable] = None

    def set_update_callback(self, callback: Callable[[dict], None]):
        """Called with the full telemetry dict on every Arduino update."""
        self._on_update = callback

    def set_estop_callback(self, callback: Callable):
        """Called when dashboard keepalive times out — triggers safe stop."""
        self._estop_callback = callback

    # ── Arduino telemetry ingest ─────────────────────────────────────────────

    def ingest(self, data: dict):
        """Process a parsed telemetry dict from Arduino."""
        with self._lock:
            self._state.arduino_t_ms     = data.get("t", 0)
            self._state.yaw              = float(data.get("yaw",   0.0))
            self._state.pitch            = float(data.get("pitch", 0.0))
            self._state.roll             = float(data.get("roll",  0.0))
            self._state.lat              = float(data.get("lat",   0.0))
            self._state.lon              = float(data.get("lon",   0.0))
            self._state.gps_ok           = bool(data.get("gps_ok", 0))
            self._state.sats             = int(data.get("sats", 0))
            self._state.gps_spd          = float(data.get("gps_spd", 0.0))
            self._state.spd              = int(data.get("spd", 0))
            self._state.cmd              = str(data.get("cmd", "STOP"))
            self._state.estop            = bool(data.get("estop", 0))
            self._state.arduino_connected = True
            self._state.last_update_ts   = time.time()

        if self._on_update:
            self._on_update(self.snapshot())

    def mark_arduino_disconnected(self):
        with self._lock:
            self._state.arduino_connected = False

    # ── Dashboard keepalive ──────────────────────────────────────────────────

    def ping_dashboard(self):
        """Call this when the dashboard sends a keepalive/command."""
        self._last_dashboard_ping = time.time()

    def start_watchdog(self):
        self._watchdog_running = True
        self._watchdog_thread = threading.Thread(
            target=self._watchdog_loop, daemon=True, name="tm-watchdog"
        )
        self._watchdog_thread.start()

    def stop_watchdog(self):
        self._watchdog_running = False

    def _watchdog_loop(self):
        while self._watchdog_running:
            elapsed = time.time() - self._last_dashboard_ping
            if elapsed > config.DASHBOARD_CMD_TIMEOUT:
                log.warning(f"Dashboard keepalive timeout ({elapsed:.1f}s) — issuing safe stop")
                if self._estop_callback:
                    self._estop_callback()
                # Reset ping so we don't spam
                self._last_dashboard_ping = time.time()
            time.sleep(0.5)

    # ── State access ─────────────────────────────────────────────────────────

    def snapshot(self) -> dict:
        """Return a dict copy of the current telemetry state."""
        with self._lock:
            d = asdict(self._state)
        return d

    def get_gps(self) -> tuple:
        """Returns (lat, lon, gps_ok)."""
        with self._lock:
            return (self._state.lat, self._state.lon, self._state.gps_ok)

    def get_yaw(self) -> float:
        with self._lock:
            return self._state.yaw
