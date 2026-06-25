# api/routes_control.py
# ======================
# FastAPI REST API routes for robot control.
#
# Endpoints:
#   POST /control/command        → Send motor command
#   POST /control/mode           → Change robot mode
#   POST /control/return_home    → Trigger return-to-home
#   POST /control/estop          → Emergency stop
#   POST /control/speed          → Set motor speed
#   GET  /control/status         → Full robot status snapshot
#   GET  /control/path           → Recorded path waypoints
#   POST /control/path/reset     → Clear path history
#   GET  /video/stream           → MJPEG camera stream
#   WS   /ws                     → WebSocket telemetry

from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from utils.logger import get_logger

log = get_logger("routes_control")


# ── Pydantic schemas ─────────────────────────────────────────────────────────

class CommandRequest(BaseModel):
    command: str = Field(..., description="Motor command: FORWARD/BACKWARD/LEFT/RIGHT/STOP")
    speed: Optional[int] = Field(None, ge=0, le=255, description="Speed 0-255")

class ModeRequest(BaseModel):
    mode: str = Field(..., description="Mode: IDLE/MANUAL/AUTONOMOUS/RETURN_HOME")

class SpeedRequest(BaseModel):
    speed: int = Field(..., ge=0, le=255)


# ── Router factory ────────────────────────────────────────────────────────────

def create_control_router(app_state: dict) -> APIRouter:
    """
    Create and return the control router.
    app_state must contain: serial_bridge, state_machine, telemetry_manager,
                             path_logger, return_manager, video_stream, autonomy_ctrl
    """
    router = APIRouter()

    serial_bridge   = app_state["serial_bridge"]
    sm              = app_state["state_machine"]
    tm              = app_state["telemetry_manager"]
    path_logger     = app_state["path_logger"]
    return_manager  = app_state["return_manager"]
    video_stream    = app_state["video_stream"]

    ALLOWED_COMMANDS = {"FORWARD", "BACKWARD", "LEFT", "RIGHT", "STOP"}

    def _send(cmd: str):
        serial_bridge.send_command(cmd)
        tm.ping_dashboard()

    # ── Control Endpoints ─────────────────────────────────────────────────────

    @router.post("/control/command")
    async def send_command(req: CommandRequest):
        cmd = req.command.upper()
        if cmd not in ALLOWED_COMMANDS:
            raise HTTPException(400, f"Unknown command: {cmd}")

        # Guard: only allow motion in MANUAL mode
        from services.state_machine import RobotMode
        if cmd != "STOP" and sm.mode not in (RobotMode.MANUAL,):
            raise HTTPException(409, f"Cannot send motion command in mode: {sm.mode_str}")

        if req.speed is not None and cmd in ("FORWARD", "BACKWARD", "LEFT", "RIGHT"):
            _send(f"{cmd} {req.speed}")
        else:
            _send(cmd)

        # Record waypoint during manual operation
        lat, lon, gps_ok = tm.get_gps()
        path_logger.record(
            lat=lat, lon=lon, gps_ok=gps_ok,
            yaw=tm.get_yaw(), mode="MANUAL", cmd=cmd,
            prev_cmd=cmd, dt=0.1
        )

        return {"status": "ok", "sent": cmd}

    @router.post("/control/mode")
    async def set_mode(req: ModeRequest):
        from services.state_machine import RobotMode
        try:
            new_mode = RobotMode(req.mode.upper())
        except ValueError:
            raise HTTPException(400, f"Unknown mode: {req.mode}")

        success = sm.transition(new_mode)
        if not success:
            raise HTTPException(409, f"Cannot transition from {sm.mode_str} to {req.mode}")

        # If switching to MANUAL, send STOP first
        if new_mode == RobotMode.MANUAL:
            _send("STOP")

        return {"status": "ok", "mode": sm.mode_str}

    @router.post("/control/return_home")
    async def return_home():
        from services.state_machine import RobotMode

        if not path_logger.waypoints:
            raise HTTPException(409, "No path recorded — cannot return home")

        # Stop current motion
        _send("STOP")

        # Build reverse path
        rev_path = path_logger.get_reverse_path()
        lat, lon, gps_ok = tm.get_gps()

        return_manager.start(
            reverse_path=rev_path,
            current_x=path_logger._local_x,
            current_y=path_logger._local_y,
            current_lat=lat, current_lon=lon,
        )

        success = sm.transition(RobotMode.RETURN_HOME)
        if not success:
            return_manager.stop()
            raise HTTPException(409, f"Cannot enter RETURN_HOME from {sm.mode_str}")

        return {"status": "ok", "waypoints": len(rev_path)}

    @router.post("/control/estop")
    async def emergency_stop():
        sm.force_estop()
        serial_bridge.send_command("ESTOP")
        return {"status": "ok", "mode": "ESTOP"}

    @router.post("/control/speed")
    async def set_speed(req: SpeedRequest):
        _send(f"SET_SPEED {req.speed}")
        return {"status": "ok", "speed": req.speed}

    # ── Status Endpoints ──────────────────────────────────────────────────────

    @router.get("/control/status")
    async def get_status():
        telemetry = tm.snapshot()
        return {
            "mode":              sm.mode_str,
            "telemetry":         telemetry,
            "serial_connected":  serial_bridge.is_connected,
            "camera_ok":         video_stream.is_ok,
            "waypoint_count":    len(path_logger.waypoints),
            "rth_active":        return_manager.is_active,
            "rth_home_reached":  return_manager.home_reached,
        }

    @router.get("/control/path")
    async def get_path():
        return {"path": path_logger.get_path_for_dashboard()}

    @router.post("/control/path/reset")
    async def reset_path():
        path_logger.reset()
        return {"status": "ok"}

    # ── Video Stream ──────────────────────────────────────────────────────────

    @router.get("/video/stream")
    async def video_stream_endpoint():
        return StreamingResponse(
            video_stream.mjpeg_generator(),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )

    return router
