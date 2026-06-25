# video/video_stream.py
# ======================
# MJPEG camera streaming for Raspberry Pi Camera.
# Uses OpenCV VideoCapture; streams via FastAPI StreamingResponse.
# Also maintains a shared latest-frame for use by the autonomy module.
#
# Dashboard accesses video at: GET /video/stream
# The <img> tag can use this URL directly — no WebRTC needed.

import asyncio
import threading
import time
from typing import Optional, Generator

import cv2
import numpy as np

import config
from utils.logger import get_logger

log = get_logger("video_stream")


class VideoStream:
    """
    Captures frames from Pi camera in a background thread.
    Serves MJPEG via async generator.
    Shares latest frame for the autonomy loop.
    """

    def __init__(self):
        self._cap: Optional[cv2.VideoCapture] = None
        self._latest_frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._frame_count = 0
        self._camera_ok = False

    def start(self):
        self._running = True
        self._thread = threading.Thread(
            target=self._capture_loop, daemon=True, name="camera-capture"
        )
        self._thread.start()
        log.info(f"Camera capture started (index={config.CAMERA_INDEX}, "
                 f"{config.CAMERA_WIDTH}x{config.CAMERA_HEIGHT} @ {config.CAMERA_FPS}fps)")

    def stop(self):
        self._running = False
        if self._cap:
            self._cap.release()
        log.info("Camera capture stopped")

    @property
    def is_ok(self) -> bool:
        return self._camera_ok

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Returns the most recent camera frame (for autonomy use)."""
        with self._lock:
            return self._latest_frame.copy() if self._latest_frame is not None else None

    def mjpeg_generator(self) -> Generator[bytes, None, None]:
        """
        Async-compatible MJPEG frame generator.
        Each yielded chunk is a complete multipart MJPEG frame boundary.
        """
        boundary = b"--frame"
        while self._running:
            frame = self.get_latest_frame()
            if frame is None:
                time.sleep(0.05)
                continue

            ret, jpeg = cv2.imencode(
                ".jpg", frame,
                [cv2.IMWRITE_JPEG_QUALITY, config.MJPEG_QUALITY]
            )
            if not ret:
                continue

            jpg_bytes = jpeg.tobytes()
            yield (
                boundary + b"\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(jpg_bytes)).encode() + b"\r\n\r\n" +
                jpg_bytes + b"\r\n"
            )
            # Throttle to target FPS
            time.sleep(1.0 / config.CAMERA_FPS)

    # ── Private ──────────────────────────────────────────────────────────────

    def _capture_loop(self):
        while self._running:
            if self._cap is None or not self._cap.isOpened():
                self._open_camera()
                if not self._camera_ok:
                    time.sleep(3.0)
                    continue

            ret, frame = self._cap.read()
            if not ret:
                log.warning("Camera read failed — reconnecting...")
                self._camera_ok = False
                if self._cap:
                    self._cap.release()
                    self._cap = None
                time.sleep(1.0)
                continue

            with self._lock:
                self._latest_frame = frame
            self._frame_count += 1
            self._camera_ok = True

    def _open_camera(self):
        log.info(f"Opening camera {config.CAMERA_INDEX}...")
        self._cap = cv2.VideoCapture(config.CAMERA_INDEX)
        if not self._cap.isOpened():
            log.error(f"Cannot open camera {config.CAMERA_INDEX}")
            self._camera_ok = False
            return

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH,  config.CAMERA_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
        self._cap.set(cv2.CAP_PROP_FPS,          config.CAMERA_FPS)
        # Pi camera: use V4L2 backend if available
        self._camera_ok = True
        log.info("Camera opened successfully")
