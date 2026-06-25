# services/serial_bridge.py
# =========================
# Async serial communication bridge between Raspberry Pi and Arduino UNO
# - Reads JSON telemetry lines from Arduino at 115200 baud
# - Sends text commands to Arduino
# - Handles reconnection automatically

import asyncio
import json
import threading
import time
from typing import Optional, Callable

import serial
import serial.tools.list_ports

import config
from utils.logger import get_logger

log = get_logger("serial_bridge")


class SerialBridge:
    """
    Thread-safe serial bridge.
    Runs a background thread for reading; command sending is thread-safe.
    """

    def __init__(self):
        self._ser: Optional[serial.Serial] = None
        self._connected = False
        self._lock = threading.Lock()
        self._read_thread: Optional[threading.Thread] = None
        self._running = False

        # Callback: called with parsed dict on each received telemetry line
        self._on_telemetry: Optional[Callable[[dict], None]] = None

    def set_telemetry_callback(self, callback: Callable[[dict], None]):
        self._on_telemetry = callback

    def start(self):
        """Start the serial bridge background thread."""
        self._running = True
        self._read_thread = threading.Thread(
            target=self._run_loop, daemon=True, name="serial-bridge"
        )
        self._read_thread.start()
        log.info(f"Serial bridge started (port={config.SERIAL_PORT}, baud={config.SERIAL_BAUD})")

    def stop(self):
        self._running = False
        if self._ser:
            try:
                self._ser.close()
            except Exception:
                pass
        log.info("Serial bridge stopped")

    @property
    def is_connected(self) -> bool:
        return self._connected

    def send_command(self, cmd: str):
        """
        Send a command string to Arduino.
        Automatically appends newline. Thread-safe.
        """
        if not self._connected:
            log.warning(f"Serial not connected — command dropped: {cmd}")
            return
        line = (cmd.strip() + "\n").encode("ascii")
        with self._lock:
            try:
                self._ser.write(line)
            except serial.SerialException as e:
                log.error(f"Serial write error: {e}")
                self._connected = False

    # ── Private ──────────────────────────────────────────────────────────────

    def _connect(self) -> bool:
        try:
            self._ser = serial.Serial(
                port=config.SERIAL_PORT,
                baudrate=config.SERIAL_BAUD,
                timeout=config.SERIAL_TIMEOUT,
            )
            # Wait for Arduino to reset after DTR toggle
            time.sleep(2.5)
            self._ser.reset_input_buffer()
            self._connected = True
            log.info(f"Connected to Arduino on {config.SERIAL_PORT}")
            return True
        except serial.SerialException as e:
            log.warning(f"Serial connect failed: {e}")
            self._connected = False
            return False

    def _run_loop(self):
        """Main background read loop with auto-reconnect."""
        while self._running:
            if not self._connected:
                if not self._connect():
                    time.sleep(config.SERIAL_RECONNECT_DELAY)
                    continue

            try:
                line_bytes = self._ser.readline()
                if not line_bytes:
                    continue

                line = line_bytes.decode("ascii", errors="replace").strip()
                if not line:
                    continue

                # Skip non-JSON lines (startup messages, errors)
                if not line.startswith("{"):
                    log.debug(f"Arduino: {line}")
                    continue

                try:
                    data = json.loads(line)
                    if self._on_telemetry:
                        self._on_telemetry(data)
                except json.JSONDecodeError:
                    log.debug(f"Invalid JSON from Arduino: {line[:80]}")

            except serial.SerialException as e:
                log.error(f"Serial read error: {e} — reconnecting...")
                self._connected = False
                try:
                    self._ser.close()
                except Exception:
                    pass
                time.sleep(config.SERIAL_RECONNECT_DELAY)

            except Exception as e:
                log.error(f"Unexpected serial error: {e}")
                time.sleep(0.5)
