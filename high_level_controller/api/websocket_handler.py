# api/websocket_handler.py
# =========================
# FastAPI WebSocket handler for real-time telemetry, log, and state broadcasting.
#
# WebSocket message format (JSON):
#   { "type": "telemetry", "data": {...} }
#   { "type": "log",       "data": {"ts":"...", "level":"INFO", "msg":"..."} }
#   { "type": "mode",      "data": {"mode": "AUTONOMOUS"} }
#   { "type": "path",      "data": [{"lat":..., "lon":..., ...}, ...] }
#   { "type": "ping",      "data": {} }  ← server-side keepalive
#
# Clients send:
#   { "type": "keepalive" }               ← dashboard heartbeat
#   { "type": "subscribe", "topics": [...] }  ← optional topic filter

import asyncio
import json
import time
from typing import Set, Optional, Callable, Any

from fastapi import WebSocket, WebSocketDisconnect

from utils.logger import get_logger

log = get_logger("websocket_handler")


class ConnectionManager:
    """Manages all active WebSocket connections and broadcast."""

    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self._connections.add(ws)
        log.info(f"WebSocket connected: {ws.client} (total: {len(self._connections)})")

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            self._connections.discard(ws)
        log.info(f"WebSocket disconnected (remaining: {len(self._connections)})")

    async def broadcast(self, msg_type: str, data: Any):
        """Broadcast a message to all connected clients."""
        payload = json.dumps({"type": msg_type, "data": data})
        dead: Set[WebSocket] = set()

        async with self._lock:
            clients = set(self._connections)

        for ws in clients:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.discard(ws)

    @property
    def client_count(self) -> int:
        return len(self._connections)


# Global connection manager instance
manager = ConnectionManager()


async def broadcast(msg_type: str, data: Any):
    """Module-level broadcast helper used by other modules."""
    await manager.broadcast(msg_type, data)


async def handle_websocket(
    ws: WebSocket,
    keepalive_callback: Optional[Callable] = None
):
    """
    Handle a single WebSocket client connection lifecycle.
    keepalive_callback: called when client sends "keepalive" message.
    """
    await manager.connect(ws)
    try:
        while True:
            try:
                # Wait for client messages with timeout
                text = await asyncio.wait_for(ws.receive_text(), timeout=30.0)
                msg = json.loads(text)
                msg_type = msg.get("type")

                if msg_type == "keepalive":
                    if keepalive_callback:
                        keepalive_callback()
                    await ws.send_text(json.dumps({"type": "pong", "data": {"ts": time.time()}}))

                elif msg_type == "subscribe":
                    # Future: implement topic filtering per client
                    pass

            except asyncio.TimeoutError:
                # Send server-side ping to keep connection alive
                try:
                    await ws.send_text(json.dumps({"type": "ping", "data": {}}))
                except Exception:
                    break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        log.warning(f"WebSocket error: {e}")
    finally:
        await manager.disconnect(ws)
