# main.py
# ========
# Quad Falcon 2 — Raspberry Pi High-Level Controller Entry Point
# FastAPI application with async startup/shutdown lifecycle.
#
# Run with:
#   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
#
# Architecture:
#   SerialBridge (thread) → TelemetryManager → WebSocket broadcast
#   VideoStream  (thread) → MJPEG endpoint + AutonomyController
#   AutonomyController (async task) → StateMachine + PathLogger + ReturnManager
#   FastAPI REST API → control endpoints
#   FastAPI WebSocket → real-time telemetry push to dashboard

import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

import config
from api.routes_control import create_control_router
from api.websocket_handler import handle_websocket, broadcast, manager
from autonomy.autonomous_controller import AutonomousController
from fusion.visual_odometry_orb import VisualOdometryORB
from services.serial_bridge import SerialBridge
from services.state_machine import StateMachine, RobotMode
from services.telemetry_manager import TelemetryManager
from services.path_logger import PathLogger
from services.return_manager import ReturnManager
from video.video_stream import VideoStream
from utils.logger import get_logger, set_ws_broadcast_callback

log = get_logger("main")

# ── Application state container ──────────────────────────────────────────────
app_state: dict = {}


# ── Lifespan: startup and shutdown ───────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("=== Quad Falcon 2 Brain Starting ===")

    # Instantiate all services
    serial_bridge  = SerialBridge()
    telemetry_mgr  = TelemetryManager()
    state_machine  = StateMachine()
    path_logger    = PathLogger()
    return_manager = ReturnManager(send_cmd_fn=serial_bridge.send_command)
    video_stream   = VideoStream()

    # Autonomy controller
    autonomy_ctrl = AutonomousController(
        state_machine=state_machine,
        telemetry_manager=telemetry_mgr,
        path_logger=path_logger,
        return_manager=return_manager,
        send_cmd_fn=serial_bridge.send_command,
        get_frame_fn=video_stream.get_latest_frame,
    )

    # Populate shared app_state for routes
    app_state.update({
        "serial_bridge":   serial_bridge,
        "state_machine":   state_machine,
        "telemetry_manager": telemetry_mgr,
        "path_logger":     path_logger,
        "return_manager":  return_manager,
        "video_stream":    video_stream,
        "autonomy_ctrl":   autonomy_ctrl,
    })

    # ── Wire up callbacks ────────────────────────────────────────────────────

    async def _broadcast_log(msg_type: str, data: dict):
        await broadcast(msg_type, data)

    set_ws_broadcast_callback(_broadcast_log)

    async def _on_telemetry(snapshot: dict):
        """Broadcast telemetry + mode + path to all WebSocket clients."""
        snapshot["mode"] = state_machine.mode_str
        snapshot["nav_decision"] = autonomy_ctrl.get_last_nav_decision()
        await broadcast("telemetry", snapshot)

    telemetry_mgr.set_update_callback(
        lambda snap: asyncio.get_event_loop().call_soon_threadsafe(
            lambda: asyncio.ensure_future(_on_telemetry(snap))
        )
    )

    def _on_serial_telemetry(data: dict):
        telemetry_mgr.ingest(data)

    serial_bridge.set_telemetry_callback(_on_serial_telemetry)

    def _safe_stop():
        serial_bridge.send_command("STOP")

    telemetry_mgr.set_estop_callback(_safe_stop)

    def _on_mode_change(old_mode: RobotMode, new_mode: RobotMode):
        asyncio.get_event_loop().call_soon_threadsafe(
            lambda: asyncio.ensure_future(broadcast("mode", {"mode": new_mode.value}))
        )

    state_machine.set_mode_change_callback(_on_mode_change)

    # ── Start services ───────────────────────────────────────────────────────
    serial_bridge.start()
    video_stream.start()
    telemetry_mgr.start_watchdog()

    # Transition to IDLE to signal readiness
    state_machine.transition(RobotMode.IDLE)

    # Start autonomy loop as background task
    autonomy_task = asyncio.create_task(autonomy_ctrl.run(), name="autonomy-loop")

    # Start telemetry broadcaster (in case Arduino is quiet, broadcast at interval)
    broadcaster_task = asyncio.create_task(_telemetry_broadcaster(telemetry_mgr, state_machine, autonomy_ctrl))

    log.info("=== Quad Falcon 2 Brain Ready ===")

    yield  # ← FastAPI runs here

    # ── Shutdown ─────────────────────────────────────────────────────────────
    log.info("Shutting down...")
    autonomy_ctrl.stop()
    autonomy_task.cancel()
    broadcaster_task.cancel()
    serial_bridge.send_command("STOP")
    serial_bridge.stop()
    video_stream.stop()
    telemetry_mgr.stop_watchdog()
    path_logger.save_to_disk()
    log.info("Shutdown complete")


async def _telemetry_broadcaster(tm: TelemetryManager, sm: StateMachine, ac: AutonomousController):
    """Periodically broadcast telemetry even if no new Arduino data arrives."""
    interval = 1.0 / config.TELEMETRY_BROADCAST_HZ
    while True:
        try:
            snap = tm.snapshot()
            snap["mode"] = sm.mode_str
            snap["nav_decision"] = ac.get_last_nav_decision()
            if manager.client_count > 0:
                await broadcast("telemetry", snap)
        except Exception as e:
            log.debug(f"Broadcaster error: {e}")
        await asyncio.sleep(interval)


# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Quad Falcon 2 Robot Brain",
    version="1.0.0",
    description="Raspberry Pi 3B high-level robot controller API",
    lifespan=lifespan,
)

# CORS — allow laptop dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routes ───────────────────────────────────────────────────────────
# Routes are created after lifespan injects app_state
@app.on_event("startup")
async def _register_routes():
    control_router = create_control_router(app_state)
    app.include_router(control_router)


@app.get("/")
async def root():
    return {
        "name": "Quad Falcon 2",
        "status": "online",
        "mode": app_state.get("state_machine", {}).mode_str if app_state else "unknown",
    }


@app.get("/health")
async def health():
    sm = app_state.get("state_machine")
    sb = app_state.get("serial_bridge")
    vs = app_state.get("video_stream")
    return {
        "status": "ok",
        "mode":           sm.mode_str if sm else "unknown",
        "serial":         sb.is_connected if sb else False,
        "camera":         vs.is_ok if vs else False,
        "ws_clients":     manager.client_count,
    }


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    tm = app_state.get("telemetry_manager")
    await handle_websocket(
        ws,
        keepalive_callback=tm.ping_dashboard if tm else None
    )
