// src/services/websocket.ts
// WebSocket client for real-time telemetry from Raspberry Pi
// Auto-reconnects on disconnect. Broadcasts events via callbacks.

import type { Telemetry, LogEntry, RobotMode, WsMessage, Waypoint } from '../types/robot';

const PI_WS_URL =
  import.meta.env.VITE_PI_WS_URL ||
  `ws://${window.location.hostname === 'localhost' ? 'raspberrypi.local' : window.location.hostname}:8000/ws`;

type TelemetryCallback   = (data: Telemetry) => void;
type LogCallback         = (entry: LogEntry) => void;
type ModeCallback        = (mode: RobotMode) => void;
type ConnectionCallback  = (connected: boolean) => void;
type PathCallback        = (path: Waypoint[]) => void;

class RobotWebSocket {
  private ws:          WebSocket | null = null;
  private reconnectTimer: number | null = null;
  private keepaliveTimer: number | null = null;
  private _connected = false;

  private onTelemetry:    TelemetryCallback   | null = null;
  private onLog:          LogCallback          | null = null;
  private onMode:         ModeCallback         | null = null;
  private onConnection:   ConnectionCallback   | null = null;
  private onPath:         PathCallback         | null = null;

  constructor() {
    this.connect();
  }

  // ── Subscription setters ──────────────────────────────────────────────────
  setTelemetryCallback(cb: TelemetryCallback)   { this.onTelemetry  = cb; }
  setLogCallback(cb: LogCallback)                { this.onLog        = cb; }
  setModeCallback(cb: ModeCallback)              { this.onMode       = cb; }
  setConnectionCallback(cb: ConnectionCallback)  { this.onConnection = cb; }
  setPathCallback(cb: PathCallback)              { this.onPath       = cb; }

  get isConnected() { return this._connected; }

  // ── Connection management ─────────────────────────────────────────────────
  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    console.log(`[WS] Connecting to ${PI_WS_URL}...`);
    this.ws = new WebSocket(PI_WS_URL);

    this.ws.onopen = () => {
      console.log('[WS] Connected');
      this._connected = true;
      this.onConnection?.(true);
      this._startKeepalive();
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const msg: WsMessage = JSON.parse(event.data as string);
        this._handleMessage(msg);
      } catch {
        // ignore malformed
      }
    };

    this.ws.onclose = () => {
      console.warn('[WS] Disconnected — reconnecting in 3s...');
      this._connected = false;
      this.onConnection?.(false);
      this._stopKeepalive();
      this.reconnectTimer = window.setTimeout(() => this.connect(), 3000);
    };

    this.ws.onerror = (e) => {
      console.error('[WS] Error', e);
    };
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this._stopKeepalive();
    this.ws?.close();
    this.ws = null;
  }

  // ── Private ───────────────────────────────────────────────────────────────

  private _handleMessage(msg: WsMessage) {
    switch (msg.type) {
      case 'telemetry':
        this.onTelemetry?.(msg.data as Telemetry);
        break;
      case 'log':
        this.onLog?.(msg.data as LogEntry);
        break;
      case 'mode':
        this.onMode?.((msg.data as { mode: RobotMode }).mode);
        break;
      case 'path':
        this.onPath?.(msg.data as Waypoint[]);
        break;
      case 'ping':
        // Server-side ping — respond with keepalive
        this._sendKeepalive();
        break;
    }
  }

  private _startKeepalive() {
    this.keepaliveTimer = window.setInterval(() => this._sendKeepalive(), 2000);
  }

  private _stopKeepalive() {
    if (this.keepaliveTimer) {
      clearInterval(this.keepaliveTimer);
      this.keepaliveTimer = null;
    }
  }

  private _sendKeepalive() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'keepalive' }));
    }
  }
}

// Singleton instance
export const robotWS = new RobotWebSocket();
