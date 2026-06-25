// src/pages/Dashboard.tsx
// Main dashboard layout: left panel | center (video+path) | right panel + bottom logs

import { StatusBar } from '../components/StatusBar';
import { ControlPad } from '../components/ControlPad';
import { SpeedSlider } from '../components/SpeedSlider';
import { ModeControls } from '../components/ModeControls';
import { VideoPanel } from '../components/VideoPanel';
import { TelemetryPanel } from '../components/TelemetryPanel';
import { PathTracker } from '../components/PathTracker';
import { LogsPanel } from '../components/LogsPanel';

export function Dashboard() {
  return (
    <div className="h-screen flex flex-col overflow-hidden bg-panel">
      {/* Top Status Bar */}
      <StatusBar />

      {/* Main content — fills remaining height */}
      <div className="flex-1 flex overflow-hidden p-2 gap-2 min-h-0">

        {/* ── Left Panel: Controls ───────────────────────────────────────── */}
        <aside className="w-60 shrink-0 flex flex-col gap-2">
          <div className="panel-card p-3 flex-none">
            <ModeControls />
          </div>
          <div className="panel-card p-3 flex-none">
            <SpeedSlider />
          </div>
          <div className="panel-card p-3 flex-none">
            <ControlPad />
          </div>
          {/* Spacer */}
          <div className="flex-1" />
          {/* Quick stats footer */}
          <QuickStats />
        </aside>

        {/* ── Center: Video + Path ───────────────────────────────────────── */}
        <div className="flex-1 flex flex-col gap-2 min-w-0 min-h-0">
          {/* Video — takes most of the height */}
          <div className="flex-1 min-h-0">
            <VideoPanel />
          </div>
          {/* Path Tracker below video */}
          <PathTracker />
        </div>

        {/* ── Right Panel: Telemetry ─────────────────────────────────────── */}
        <aside className="w-56 shrink-0 flex flex-col gap-2 overflow-y-auto">
          <TelemetryPanel />
        </aside>
      </div>

      {/* Bottom Logs Bar */}
      <div className="h-40 shrink-0 border-t border-panel-border mx-2 mb-2">
        <LogsPanel />
      </div>
    </div>
  );
}

function QuickStats() {
  return (
    <div className="panel-card p-2 text-xs text-muted space-y-1">
      <div className="flex justify-between">
        <span>Serial Baud</span>
        <span className="font-mono text-white">115200</span>
      </div>
      <div className="flex justify-between">
        <span>Telem Rate</span>
        <span className="font-mono text-white">10 Hz</span>
      </div>
      <div className="flex justify-between">
        <span>Camera</span>
        <span className="font-mono text-white">640×480</span>
      </div>
    </div>
  );
}
