// src/components/StatusBar.tsx
// Top status bar showing connection status, mode badge, and system time

import { useRobotStore } from '../store/robotStore';
import { Wifi, WifiOff, Cpu, Camera, Clock } from 'lucide-react';
import clsx from 'clsx';

const MODE_COLORS: Record<string, string> = {
  IDLE:        'bg-muted/20 text-muted border-muted/30',
  MANUAL:      'bg-accent/20 text-accent border-accent/40',
  AUTONOMOUS:  'bg-success/20 text-success border-success/40',
  RETURN_HOME: 'bg-warning/20 text-warning border-warning/40',
  ESTOP:       'bg-danger/20 text-danger border-danger/40 animate-pulse',
};

export function StatusBar() {
  const { wsConnected, arduinoConnected, cameraOk, mode } = useRobotStore();

  const now = new Date().toLocaleTimeString();

  return (
    <header className="h-12 bg-panel-light border-b border-panel-border flex items-center px-4 gap-4 shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2 mr-2">
        <div className="w-7 h-7 rounded-full bg-accent/20 border border-accent/40 flex items-center justify-center">
          <span className="text-accent text-xs font-bold">QF</span>
        </div>
        <span className="text-sm font-semibold text-white tracking-tight">Quad Falcon 2</span>
        <span className="text-xs text-muted">Control Center</span>
      </div>

      <div className="h-5 w-px bg-panel-border" />

      {/* Mode Badge */}
      <span
        id="mode-badge"
        className={clsx(
          'px-3 py-0.5 rounded-full border text-xs font-semibold uppercase tracking-widest transition-all',
          MODE_COLORS[mode] ?? MODE_COLORS.IDLE
        )}
      >
        {mode}
      </span>

      <div className="flex-1" />

      {/* Connection indicators */}
      <div className="flex items-center gap-3 text-xs">
        {/* WebSocket / Pi */}
        <Indicator
          id="ws-indicator"
          icon={wsConnected ? Wifi : WifiOff}
          label="Pi"
          ok={wsConnected}
        />
        {/* Arduino */}
        <Indicator
          id="arduino-indicator"
          icon={Cpu}
          label="Arduino"
          ok={arduinoConnected}
        />
        {/* Camera */}
        <Indicator
          id="camera-indicator"
          icon={Camera}
          label="Camera"
          ok={cameraOk}
        />

        <div className="h-4 w-px bg-panel-border" />

        {/* Clock */}
        <div className="flex items-center gap-1.5 text-muted">
          <Clock size={13} />
          <span className="font-mono">{now}</span>
        </div>
      </div>
    </header>
  );
}

function Indicator({
  icon: Icon, label, ok, id,
}: {
  icon: React.ElementType; label: string; ok: boolean; id: string;
}) {
  return (
    <div id={id} className="flex items-center gap-1.5">
      <div className={clsx('w-1.5 h-1.5 rounded-full', ok ? 'bg-success animate-pulse-slow' : 'bg-danger')} />
      <Icon size={13} className={ok ? 'text-success' : 'text-danger'} />
      <span className={ok ? 'text-success' : 'text-muted'}>{label}</span>
    </div>
  );
}
