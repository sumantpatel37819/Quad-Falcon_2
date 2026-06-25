// src/services/api.ts
// REST API client for Raspberry Pi backend

const PI_BASE = import.meta.env.VITE_PI_URL || '';  // Empty = use Vite proxy

async function fetchJSON<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${PI_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${path} failed (${res.status}): ${text}`);
  }
  return res.json() as Promise<T>;
}

// ── Motor Control ─────────────────────────────────────────────────────────────

export const api = {
  /** Send a motion command to the robot */
  sendCommand: (command: string, speed?: number) =>
    fetchJSON('/control/command', {
      method: 'POST',
      body: JSON.stringify({ command, speed }),
    }),

  /** Change robot operating mode */
  setMode: (mode: string) =>
    fetchJSON('/control/mode', {
      method: 'POST',
      body: JSON.stringify({ mode }),
    }),

  /** Trigger return-to-home */
  returnHome: () =>
    fetchJSON('/control/return_home', { method: 'POST' }),

  /** Emergency stop */
  estop: () =>
    fetchJSON('/control/estop', { method: 'POST' }),

  /** Set motor speed (0–255) */
  setSpeed: (speed: number) =>
    fetchJSON('/control/speed', {
      method: 'POST',
      body: JSON.stringify({ speed }),
    }),

  /** Get full robot status */
  getStatus: () =>
    fetchJSON<{
      mode: string;
      serial_connected: boolean;
      camera_ok: boolean;
      waypoint_count: number;
      rth_active: boolean;
    }>('/control/status'),

  /** Get recorded path waypoints */
  getPath: () =>
    fetchJSON<{ path: unknown[] }>('/control/path'),

  /** Reset path history */
  resetPath: () =>
    fetchJSON('/control/path/reset', { method: 'POST' }),

  /** Health check */
  health: () => fetchJSON('/health'),

  /** MJPEG video stream URL (used directly in <img src> tag) */
  videoStreamUrl: () => `${PI_BASE}/video/stream`,
};
