// src/components/TelemetryPanel.tsx
// Live telemetry display with IMU, GPS, motor, and autonomy data

import { useRobotStore } from '../store/robotStore';
import { Navigation, MapPin, Cpu, Activity, Eye } from 'lucide-react';
import clsx from 'clsx';

function MetricRow({ label, value, unit = '', ok = true }: {
  label: string; value: string | number; unit?: string; ok?: boolean;
}) {
  return (
    <div className="flex items-baseline justify-between py-1 border-b border-panel-border/50 last:border-0">
      <span className="tele-label">{label}</span>
      <span className={clsx('tele-value text-sm', !ok && 'text-muted')}>
        {value}
        {unit && <span className="text-muted text-xs ml-1">{unit}</span>}
      </span>
    </div>
  );
}

function Section({ title, icon, children }: {
  title: string; icon: React.ReactNode; children: React.ReactNode;
}) {
  return (
    <div className="metric-card">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-accent">{icon}</span>
        <span className="text-xs font-semibold uppercase tracking-wider text-muted">{title}</span>
      </div>
      <div className="space-y-0.5">{children}</div>
    </div>
  );
}

const NAV_DECISION_COLOR: Record<string, string> = {
  FORWARD:   'text-success',
  TURN_LEFT:  'text-warning',
  TURN_RIGHT: 'text-warning',
  STOP_SCAN:  'text-danger',
  UNKNOWN:    'text-muted',
};

export function TelemetryPanel() {
  const { telemetry, mode } = useRobotStore();
  const t = telemetry;

  return (
    <div className="space-y-2 overflow-y-auto">
      <p className="section-label px-1">Live Telemetry</p>

      {/* IMU */}
      <Section title="IMU / Heading" icon={<Navigation size={13} />}>
        <MetricRow label="Yaw"   value={t.yaw.toFixed(1)}   unit="°" />
        <MetricRow label="Pitch" value={t.pitch.toFixed(1)} unit="°" />
        <MetricRow label="Roll"  value={t.roll.toFixed(1)}  unit="°" />
      </Section>

      {/* GPS */}
      <Section title="GPS" icon={<MapPin size={13} />}>
        <MetricRow label="Latitude"  value={t.gps_ok ? t.lat.toFixed(6) : '—'} ok={t.gps_ok} />
        <MetricRow label="Longitude" value={t.gps_ok ? t.lon.toFixed(6) : '—'} ok={t.gps_ok} />
        <MetricRow
          label="Status"
          value={t.gps_ok ? `Fix (${t.sats} sats)` : 'No Fix'}
          ok={t.gps_ok}
        />
        <MetricRow label="GPS Speed" value={t.gps_spd.toFixed(1)} unit="km/h" />
      </Section>

      {/* Motor */}
      <Section title="Motor" icon={<Cpu size={13} />}>
        <MetricRow label="Speed"    value={t.spd} unit="/255" />
        <MetricRow label="Last Cmd" value={t.cmd} />
        <MetricRow label="E-Stop"   value={t.estop ? 'ACTIVE' : 'Clear'} ok={!t.estop} />
      </Section>

      {/* Autonomy */}
      <Section title="Autonomy" icon={<Eye size={13} />}>
        <div className="flex items-baseline justify-between py-1 border-b border-panel-border/50">
          <span className="tele-label">Decision</span>
          <span className={clsx('font-mono text-sm font-semibold', NAV_DECISION_COLOR[t.nav_decision] ?? 'text-muted')}>
            {t.nav_decision}
          </span>
        </div>
        <MetricRow label="Mode"    value={mode} />
      </Section>

      {/* System */}
      <Section title="System" icon={<Activity size={13} />}>
        <MetricRow
          label="Arduino"
          value={t.arduino_connected ? 'Connected' : 'Disconnected'}
          ok={t.arduino_connected}
        />
        <MetricRow label="Uptime" value={`${(t.arduino_t_ms / 1000).toFixed(0)}`} unit="s" />
      </Section>
    </div>
  );
}
