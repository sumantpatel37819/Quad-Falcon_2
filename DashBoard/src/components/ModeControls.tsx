// src/components/ModeControls.tsx
// Mode switching, return-home, and emergency stop buttons

import { useState } from 'react';
import { Bot, Hand, Home, AlertTriangle, RotateCcw } from 'lucide-react';
import { useRobotStore } from '../store/robotStore';
import { api } from '../services/api';
import clsx from 'clsx';

export function ModeControls() {
  const { mode, setMode } = useRobotStore();
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const exec = async (label: string, fn: () => Promise<unknown>) => {
    setLoading(label);
    setError(null);
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(null);
    }
  };

  const switchMode = (newMode: string) =>
    exec(newMode, async () => {
      await api.setMode(newMode);
      setMode(newMode as Parameters<typeof setMode>[0]);
    });

  const returnHome = () =>
    exec('RTH', async () => {
      await api.returnHome();
      setMode('RETURN_HOME');
    });

  const estop = () =>
    exec('ESTOP', async () => {
      await api.estop();
      setMode('ESTOP');
    });

  const clearEstop = () =>
    exec('IDLE', () => api.setMode('IDLE'));

  const isEstop = mode === 'ESTOP';

  return (
    <div className="space-y-3">
      <p className="section-label">Robot Mode</p>

      {/* Mode buttons */}
      <div className="grid grid-cols-2 gap-2">
        <ModeButton
          id="btn-mode-manual"
          label="Manual"
          icon={<Hand size={15} />}
          active={mode === 'MANUAL'}
          disabled={isEstop || loading !== null}
          loading={loading === 'MANUAL'}
          onClick={() => switchMode('MANUAL')}
        />
        <ModeButton
          id="btn-mode-autonomous"
          label="Autonomous"
          icon={<Bot size={15} />}
          active={mode === 'AUTONOMOUS'}
          disabled={isEstop || loading !== null}
          loading={loading === 'AUTONOMOUS'}
          onClick={() => switchMode('AUTONOMOUS')}
          color="success"
        />
      </div>

      {/* Return Home */}
      <button
        id="btn-return-home"
        onClick={returnHome}
        disabled={isEstop || loading !== null}
        className={clsx(
          'btn-ghost w-full justify-center',
          mode === 'RETURN_HOME' && 'border-warning/60 text-warning bg-warning/10'
        )}
      >
        <Home size={15} />
        {loading === 'RTH' ? 'Initiating...' : 'Return to Home'}
      </button>

      {/* ESTOP / Clear */}
      {isEstop ? (
        <button
          id="btn-clear-estop"
          onClick={clearEstop}
          className="btn w-full bg-warning/20 border border-warning/40 text-warning hover:bg-warning/30"
        >
          <RotateCcw size={15} />
          Clear E-Stop
        </button>
      ) : (
        <button
          id="btn-estop"
          onClick={estop}
          disabled={loading !== null}
          className="btn-danger w-full justify-center text-base font-bold py-3"
        >
          <AlertTriangle size={18} />
          EMERGENCY STOP
        </button>
      )}

      {error && (
        <p className="text-xs text-danger bg-danger/10 border border-danger/20 rounded px-2 py-1">
          {error}
        </p>
      )}
    </div>
  );
}

function ModeButton({
  id, label, icon, active, disabled, loading, onClick, color = 'accent',
}: {
  id: string;
  label: string;
  icon: React.ReactNode;
  active: boolean;
  disabled: boolean;
  loading: boolean;
  onClick: () => void;
  color?: 'accent' | 'success';
}) {
  const colors = {
    accent:  { active: 'border-accent/60 text-accent bg-accent/15',  inactive: 'border-panel-border text-muted hover:border-accent/30' },
    success: { active: 'border-success/60 text-success bg-success/15', inactive: 'border-panel-border text-muted hover:border-success/30' },
  };

  return (
    <button
      id={id}
      onClick={onClick}
      disabled={disabled}
      className={clsx(
        'btn py-2 px-3 text-xs border transition-all',
        active ? colors[color].active : colors[color].inactive,
        disabled && 'opacity-30 cursor-not-allowed'
      )}
    >
      {icon}
      {loading ? '...' : label}
      {active && <span className="ml-auto w-1.5 h-1.5 rounded-full bg-current animate-pulse" />}
    </button>
  );
}
