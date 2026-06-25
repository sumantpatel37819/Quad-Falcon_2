# services/state_machine.py
# ==========================
# Robot finite state machine (FSM)
# States: IDLE → MANUAL ↔ AUTONOMOUS, any → RETURN_HOME, any → ESTOP
#
# Transitions are guarded to prevent invalid state changes.

from enum import Enum
import threading
import time
from typing import Optional, Callable

from utils.logger import get_logger

log = get_logger("state_machine")


class RobotMode(str, Enum):
    IDLE        = "IDLE"
    MANUAL      = "MANUAL"
    AUTONOMOUS  = "AUTONOMOUS"
    RETURN_HOME = "RETURN_HOME"
    ESTOP       = "ESTOP"


# Valid transitions: current_state → [allowed next states]
VALID_TRANSITIONS = {
    RobotMode.IDLE:        [RobotMode.MANUAL, RobotMode.AUTONOMOUS, RobotMode.RETURN_HOME, RobotMode.ESTOP],
    RobotMode.MANUAL:      [RobotMode.IDLE, RobotMode.AUTONOMOUS, RobotMode.RETURN_HOME, RobotMode.ESTOP],
    RobotMode.AUTONOMOUS:  [RobotMode.IDLE, RobotMode.MANUAL, RobotMode.RETURN_HOME, RobotMode.ESTOP],
    RobotMode.RETURN_HOME: [RobotMode.IDLE, RobotMode.MANUAL, RobotMode.ESTOP],
    RobotMode.ESTOP:       [RobotMode.IDLE, RobotMode.MANUAL],  # Must explicitly clear e-stop
}


class StateMachine:
    def __init__(self):
        self._mode = RobotMode.IDLE
        self._lock = threading.Lock()
        self._mode_change_callback: Optional[Callable[[RobotMode, RobotMode], None]] = None
        self._mode_entered_at = time.time()

    def set_mode_change_callback(self, cb: Callable[[RobotMode, RobotMode], None]):
        """Called with (old_mode, new_mode) on every valid transition."""
        self._mode_change_callback = cb

    @property
    def mode(self) -> RobotMode:
        with self._lock:
            return self._mode

    @property
    def mode_str(self) -> str:
        return self._mode.value

    def transition(self, new_mode: RobotMode) -> bool:
        """
        Attempt a state transition. Returns True if successful.
        Returns False if transition is not allowed.
        """
        with self._lock:
            current = self._mode
            if new_mode == current:
                return True  # No-op

            allowed = VALID_TRANSITIONS.get(current, [])
            if new_mode not in allowed:
                log.warning(
                    f"Invalid transition: {current.value} → {new_mode.value} "
                    f"(allowed: {[s.value for s in allowed]})"
                )
                return False

            old_mode = self._mode
            self._mode = new_mode
            self._mode_entered_at = time.time()

        log.info(f"Mode transition: {old_mode.value} → {new_mode.value}")
        if self._mode_change_callback:
            self._mode_change_callback(old_mode, new_mode)
        return True

    def force_estop(self):
        """Force e-stop regardless of current state (bypass guards)."""
        with self._lock:
            old = self._mode
            self._mode = RobotMode.ESTOP
            self._mode_entered_at = time.time()
        log.critical(f"FORCE ESTOP (was: {old.value})")
        if self._mode_change_callback:
            self._mode_change_callback(old, RobotMode.ESTOP)

    def is_motion_allowed(self) -> bool:
        """Returns True if robot is in a mode that allows motor commands."""
        return self._mode not in (RobotMode.IDLE, RobotMode.ESTOP)

    def time_in_mode(self) -> float:
        """Seconds elapsed in current mode."""
        return time.time() - self._mode_entered_at
