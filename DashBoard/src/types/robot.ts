// src/types/robot.ts
// TypeScript interfaces matching the Pi backend data structures

export type RobotMode = 'IDLE' | 'MANUAL' | 'AUTONOMOUS' | 'RETURN_HOME' | 'ESTOP';
export type NavDecision = 'FORWARD' | 'TURN_LEFT' | 'TURN_RIGHT' | 'STOP_SCAN' | 'UNKNOWN';
export type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'CRITICAL';

export interface Telemetry {
  // IMU
  yaw:   number;
  pitch: number;
  roll:  number;
  // GPS
  lat:     number;
  lon:     number;
  gps_ok:  boolean;
  sats:    number;
  gps_spd: number;
  // Motor
  spd:  number;
  cmd:  string;
  // Safety
  estop: boolean;
  // System
  arduino_t_ms:       number;
  arduino_connected:  boolean;
  last_update_ts:     number;
  // Pi-side additions
  mode:         RobotMode;
  nav_decision: NavDecision;
}

export interface Waypoint {
  timestamp:  number;
  lat:        number;
  lon:        number;
  gps_ok:     boolean;
  local_x:    number;
  local_y:    number;
  yaw:        number;
  mode:       string;
  cmd:        string;
}

export interface LogEntry {
  ts:     string;
  level:  LogLevel;
  module: string;
  msg:    string;
}

export interface RobotStatus {
  mode:            RobotMode;
  telemetry:       Telemetry;
  serial_connected: boolean;
  camera_ok:        boolean;
  waypoint_count:   number;
  rth_active:       boolean;
  rth_home_reached: boolean;
}

export interface WsMessage {
  type: 'telemetry' | 'log' | 'mode' | 'path' | 'ping' | 'pong';
  data: unknown;
}
