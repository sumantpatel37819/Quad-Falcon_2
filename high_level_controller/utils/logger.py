# utils/logger.py
# ================
# Structured logger with timestamped entries and WebSocket broadcast support

import logging
import sys
from datetime import datetime, timezone
from typing import Optional, Callable

# Global log callback for WebSocket broadcasting
_ws_broadcast_callback: Optional[Callable] = None

def set_ws_broadcast_callback(callback: Callable):
    """Register a coroutine callback for broadcasting log entries via WebSocket."""
    global _ws_broadcast_callback
    _ws_broadcast_callback = callback

def get_logger(name: str) -> "RobotLogger":
    return RobotLogger(name)

class RobotLogger:
    """Logger that writes to stderr and optionally broadcasts to WebSocket."""

    def __init__(self, name: str):
        self._name = name
        self._log = logging.getLogger(name)
        if not self._log.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter(
                "[%(asctime)s] [%(name)s] %(levelname)s: %(message)s",
                datefmt="%H:%M:%S"
            ))
            self._log.addHandler(handler)
            self._log.setLevel(logging.DEBUG)

    def _broadcast(self, level: str, msg: str):
        global _ws_broadcast_callback
        if _ws_broadcast_callback:
            import asyncio
            entry = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "level": level,
                "module": self._name,
                "msg": msg,
            }
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_ws_broadcast_callback("log", entry))
            except Exception:
                pass

    def debug(self, msg: str):
        self._log.debug(msg)

    def info(self, msg: str):
        self._log.info(msg)
        self._broadcast("INFO", msg)

    def warning(self, msg: str):
        self._log.warning(msg)
        self._broadcast("WARN", msg)

    def error(self, msg: str):
        self._log.error(msg)
        self._broadcast("ERROR", msg)

    def critical(self, msg: str):
        self._log.critical(msg)
        self._broadcast("CRITICAL", msg)
