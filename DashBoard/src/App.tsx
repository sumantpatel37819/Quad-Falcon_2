// src/App.tsx
// Root app component: wires WebSocket to Zustand store

import { useEffect } from 'react';
import { Dashboard } from './pages/Dashboard';
import { robotWS } from './services/websocket';
import { useRobotStore } from './store/robotStore';
import type { Telemetry, LogEntry, RobotMode, Waypoint } from './types/robot';

export default function App() {
  const {
    setWsConnected,
    updateTelemetry,
    addLog,
    setMode,
    addPath,
    setCameraOk,
  } = useRobotStore();

  useEffect(() => {
    // Wire WebSocket events to store
    robotWS.setConnectionCallback((connected) => {
      setWsConnected(connected);
      addLog({
        ts: new Date().toISOString(),
        level: connected ? 'INFO' : 'WARN',
        module: 'websocket',
        msg: connected ? 'Connected to robot brain' : 'Disconnected from robot brain',
      });
    });

    robotWS.setTelemetryCallback((data: Telemetry) => {
      updateTelemetry(data);
      setCameraOk(true); // If telemetry arrives, Pi is up — camera state from data
    });

    robotWS.setLogCallback((entry: LogEntry) => {
      addLog(entry);
    });

    robotWS.setModeCallback((mode: RobotMode) => {
      setMode(mode);
    });

    robotWS.setPathCallback((path: Waypoint[]) => {
      addPath(path);
    });

    // Initial connection
    robotWS.connect();

    return () => {
      robotWS.disconnect();
    };
  }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  return <Dashboard />;
}
