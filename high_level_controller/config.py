# config.py
# =========
# Quad Falcon 2 - Raspberry Pi High-Level Controller Configuration
# All tunable parameters in one place

import os

# ── Serial (Arduino connection) ──────────────────────────────────────────────
SERIAL_PORT      = os.getenv("SERIAL_PORT", "/dev/ttyUSB0")  # or /dev/ttyACM0
SERIAL_BAUD      = int(os.getenv("SERIAL_BAUD", "115200"))
SERIAL_TIMEOUT   = 1.0          # seconds read timeout
SERIAL_RECONNECT_DELAY = 3.0   # seconds between reconnect attempts

# ── FastAPI Server ───────────────────────────────────────────────────────────
HOST             = os.getenv("HOST", "0.0.0.0")
PORT             = int(os.getenv("PORT", "8000"))
CORS_ORIGINS     = [
    "http://localhost:5173",   # Vite dev server
    "http://localhost:3000",
    "*",                       # Allow all for LAN access
]

# ── Camera ───────────────────────────────────────────────────────────────────
CAMERA_INDEX     = int(os.getenv("CAMERA_INDEX", "0"))  # /dev/video0
CAMERA_WIDTH     = int(os.getenv("CAMERA_WIDTH",  "640"))
CAMERA_HEIGHT    = int(os.getenv("CAMERA_HEIGHT", "480"))
CAMERA_FPS       = int(os.getenv("CAMERA_FPS",    "15"))
MJPEG_QUALITY    = int(os.getenv("MJPEG_QUALITY", "70"))  # JPEG quality 0-100

# ── Telemetry ────────────────────────────────────────────────────────────────
TELEMETRY_BROADCAST_HZ = 10    # WebSocket broadcast rate
WS_HEARTBEAT_INTERVAL  = 5.0  # seconds

# ── Autonomy ─────────────────────────────────────────────────────────────────
AUTONOMY_LOOP_HZ     = 5       # Hz — autonomy decision loop rate
OBSTACLE_THRESHOLD   = 0.45    # free-space score below this = blocked
FORWARD_BIAS         = 0.1     # bonus score added to center sector
DEFAULT_AUTO_SPEED   = 130     # motor speed during autonomous mode
TURN_SPEED           = 110     # motor speed during turns
SCAN_TURN_DURATION   = 0.6     # seconds for scan turn if all blocked

# ── ORB Visual Odometry ──────────────────────────────────────────────────────
ORB_MAX_FEATURES     = 300
ORB_MATCH_RATIO      = 0.75    # Lowe's ratio test threshold

# ── Path Logger ──────────────────────────────────────────────────────────────
WAYPOINT_MIN_DISTANCE = 0.3    # metres — minimum distance before recording new waypoint
GPS_MIN_HDOP          = 5.0    # HDOP threshold for GPS validity
PATH_LOG_FILE         = "/tmp/quad_falcon_path.json"  # persisted on disk

# ── Return-to-Home ───────────────────────────────────────────────────────────
RTH_WAYPOINT_TOLERANCE_GPS   = 2.0    # metres — GPS waypoint reached threshold
RTH_WAYPOINT_TOLERANCE_LOCAL = 0.4    # metres — local coord waypoint threshold
RTH_HEADING_TOLERANCE        = 15.0   # degrees — heading alignment tolerance
RTH_MOVE_SPEED               = 120    # motor speed during RTH
RTH_TURN_SPEED               = 100
RTH_HOME_REACHED_RADIUS      = 1.5    # metres — home declared reached

# ── Command Timeout ──────────────────────────────────────────────────────────
DASHBOARD_CMD_TIMEOUT = 3.0    # seconds — if no keepalive, auto-stop
