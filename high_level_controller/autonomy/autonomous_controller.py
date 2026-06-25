# autonomy/autonomous_controller.py
# ==================================
# Main autonomy loop running on Raspberry Pi.
# Integrates obstacle detection, navigation decisions, and return-to-home.
# Runs as an async background task.

import asyncio
import time
from typing import Callable, Optional

import config
from autonomy.obstacle_detector import ObstacleDetector
from autonomy.free_path_selector import FreePathSelector, NavDecision
from services.state_machine import StateMachine, RobotMode
from services.path_logger import PathLogger
from services.return_manager import ReturnManager
from services.telemetry_manager import TelemetryManager
from fusion.visual_odometry_orb import VisualOdometryORB
from utils.logger import get_logger

log = get_logger("autonomous_controller")


class AutonomousController:
    """
    Runs the autonomy loop when mode is AUTONOMOUS or RETURN_HOME.
    Reads frames from the video stream shared frame store.
    """

    def __init__(
        self,
        state_machine:      StateMachine,
        telemetry_manager:  TelemetryManager,
        path_logger:        PathLogger,
        return_manager:     ReturnManager,
        send_cmd_fn:        Callable[[str], None],
        get_frame_fn:       Callable,     # Returns latest camera frame (np.ndarray or None)
    ):
        self._sm        = state_machine
        self._tm        = telemetry_manager
        self._pl        = path_logger
        self._rm        = return_manager
        self._send_cmd  = send_cmd_fn
        self._get_frame = get_frame_fn

        self._detector  = ObstacleDetector()
        self._selector  = FreePathSelector()
        self._orb       = VisualOdometryORB()

        self._running   = False
        self._scan_until: float = 0.0  # Time when scan turn ends
        self._last_nav_decision = NavDecision.UNKNOWN

        # ORB runs every N autonomy steps to save CPU
        self._orb_every_n = 5
        self._step_count  = 0

    async def run(self):
        """Main async autonomy loop. Call this as an asyncio task."""
        self._running = True
        interval = 1.0 / config.AUTONOMY_LOOP_HZ
        log.info(f"Autonomy loop started at {config.AUTONOMY_LOOP_HZ} Hz")

        while self._running:
            loop_start = time.time()
            mode = self._sm.mode

            try:
                if mode == RobotMode.AUTONOMOUS:
                    await self._autonomous_step()
                elif mode == RobotMode.RETURN_HOME:
                    await self._return_home_step()
                # MANUAL / IDLE / ESTOP: do nothing

            except Exception as e:
                log.error(f"Autonomy loop error: {e}")

            # Maintain loop rate
            elapsed = time.time() - loop_start
            sleep_time = max(0.0, interval - elapsed)
            await asyncio.sleep(sleep_time)

        log.info("Autonomy loop stopped")

    def stop(self):
        self._running = False

    # ── Autonomous navigation step ────────────────────────────────────────────

    async def _autonomous_step(self):
        telemetry = self._tm.snapshot()

        # Get latest camera frame
        frame = self._get_frame()
        if frame is None:
            log.warning("No camera frame — stopping autonomous movement")
            self._send_cmd("STOP")
            return

        # ORB visual odometry (runs every N steps)
        self._step_count += 1
        if self._step_count % self._orb_every_n == 0:
            orb_result = self._orb.process(frame)
            if orb_result.valid:
                log.debug(
                    f"ORB motion: dx={orb_result.dx_px:.1f}px, "
                    f"dy={orb_result.dy_px:.1f}px, "
                    f"rot={orb_result.rotation_deg:.1f}°"
                )

        # Obstacle detection
        report = self._detector.analyze(frame)
        nav    = self._selector.decide(report)
        self._last_nav_decision = nav.decision

        # If we're in a scan turn, continue until timer expires
        now = time.time()
        if self._scan_until > now:
            # Scan turn in progress — don't override
            return

        # Act on navigation decision
        if nav.decision == NavDecision.FORWARD:
            self._send_cmd(f"FORWARD {config.DEFAULT_AUTO_SPEED}")

        elif nav.decision == NavDecision.TURN_LEFT:
            self._send_cmd(f"LEFT {config.TURN_SPEED}")

        elif nav.decision == NavDecision.TURN_RIGHT:
            self._send_cmd(f"RIGHT {config.TURN_SPEED}")

        elif nav.decision == NavDecision.STOP_SCAN:
            # All blocked — rotate slowly to find a free direction
            log.info("All sectors blocked — initiating scan turn")
            self._send_cmd(f"RIGHT {config.TURN_SPEED}")
            self._scan_until = now + config.SCAN_TURN_DURATION

        # Record waypoint
        lat, lon, gps_ok = self._tm.get_gps()
        self._pl.record(
            lat=lat, lon=lon, gps_ok=gps_ok,
            yaw=telemetry["yaw"],
            mode="AUTONOMOUS",
            cmd=nav.decision.value,
            prev_cmd=nav.decision.value,
            dt=1.0 / config.AUTONOMY_LOOP_HZ,
        )

    # ── Return-to-home step ───────────────────────────────────────────────────

    async def _return_home_step(self):
        telemetry = self._tm.snapshot()
        lat, lon, gps_ok = self._tm.get_gps()

        if not self._rm.is_active:
            log.warning("RTH mode but ReturnManager not active — transitioning to IDLE")
            self._sm.transition(RobotMode.IDLE)
            return

        reached = self._rm.step(
            current_lat=lat, current_lon=lon, gps_ok=gps_ok,
            current_x=self._pl._local_x, current_y=self._pl._local_y,
            current_heading=telemetry["yaw"],
        )

        if reached:
            log.info("RTH complete — transitioning to IDLE")
            self._sm.transition(RobotMode.IDLE)

    def get_last_nav_decision(self) -> str:
        return self._last_nav_decision.value if self._last_nav_decision else "UNKNOWN"
