// src/store/robotStore.ts
// Zustand global state store for all robot data

import { create } from 'zustand';
import type { Telemetry, LogEntry, RobotMode, Waypoint } from '../types/robot';

const MAX_LOGS = 200;

interface RobotStore {
  // Connection
  wsConnected:    boolean;
  piConnected:    boolean;
  arduinoConnected: boolean;

  // Robot state
  mode:           RobotMode;
  telemetry:      Telemetry;
  speed:          number;   // Dashboard-controlled speed slider value

  // Path
  path:           Waypoint[];

  // Logs
  logs:           LogEntry[];

  // RTH
  rthActive:      boolean;
  homeReached:    boolean;

  // Camera
  cameraOk:       boolean;

  // ── Actions ────────────────────────────────────────────────────────────────
  setWsConnected:     (v: boolean) => void;
  setPiConnected:     (v: boolean) => void;
  setMode:            (m: RobotMode) => void;
  updateTelemetry:    (t: Telemetry) => void;
  setSpeed:           (s: number) => void;
  addPath:            (path: Waypoint[]) => void;
  appendWaypoint:     (wp: Waypoint) => void;
  addLog:             (entry: LogEntry) => void;
  clearLogs:          () => void;
  setRthActive:       (v: boolean) => void;
  setHomeReached:     (v: boolean) => void;
  setCameraOk:        (v: boolean) => void;
  resetPath:          () => void;
}

const defaultTelemetry: Telemetry = {
  yaw: 0, pitch: 0, roll: 0,
  lat: 0, lon: 0, gps_ok: false, sats: 0, gps_spd: 0,
  spd: 0, cmd: 'STOP',
  estop: false,
  arduino_t_ms: 0, arduino_connected: false, last_update_ts: 0,
  mode: 'IDLE', nav_decision: 'UNKNOWN',
};

export const useRobotStore = create<RobotStore>((set) => ({
  wsConnected:      false,
  piConnected:      false,
  arduinoConnected: false,
  mode:             'IDLE',
  telemetry:        defaultTelemetry,
  speed:            150,
  path:             [],
  logs:             [],
  rthActive:        false,
  homeReached:      false,
  cameraOk:         false,

  setWsConnected:  (v) => set({ wsConnected: v, piConnected: v }),
  setPiConnected:  (v) => set({ piConnected: v }),
  setMode:         (m) => set({ mode: m }),

  updateTelemetry: (t) =>
    set({
      telemetry:        t,
      mode:             t.mode,
      arduinoConnected: t.arduino_connected,
      rthActive:        false,  // Will be updated via status polling
    }),

  setSpeed: (s) => set({ speed: s }),

  addPath:        (path) => set({ path }),
  appendWaypoint: (wp)   => set((state) => ({ path: [...state.path, wp] })),
  resetPath:      ()     => set({ path: [] }),

  addLog: (entry) =>
    set((state) => ({
      logs: [entry, ...state.logs].slice(0, MAX_LOGS),
    })),

  clearLogs: () => set({ logs: [] }),

  setRthActive:  (v) => set({ rthActive: v }),
  setHomeReached:(v) => set({ homeReached: v }),
  setCameraOk:   (v) => set({ cameraOk: v }),
}));
