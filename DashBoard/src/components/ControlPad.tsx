// src/components/ControlPad.tsx
// D-pad style directional control with keyboard support
// Sends commands via REST API

import { useEffect, useState, useCallback } from 'react';
import { ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Square } from 'lucide-react';
import { useRobotStore } from '../store/robotStore';
import { api } from '../services/api';
import clsx from 'clsx';

type Direction = 'FORWARD' | 'BACKWARD' | 'LEFT' | 'RIGHT' | null;

const KEY_MAP: Record<string, Direction> = {
  ArrowUp:    'FORWARD',
  ArrowDown:  'BACKWARD',
  ArrowLeft:  'LEFT',
  ArrowRight: 'RIGHT',
  KeyW:       'FORWARD',
  KeyS:       'BACKWARD',
  KeyA:       'LEFT',
  KeyD:       'RIGHT',
};

export function ControlPad() {
  const { mode, speed } = useRobotStore();
  const [active, setActive] = useState<Direction>(null);
  const [error, setError] = useState<string | null>(null);
  const isManual = mode === 'MANUAL';

  const sendCmd = useCallback(async (cmd: Direction | 'STOP') => {
    try {
      if (cmd === null || cmd === 'STOP') {
        await api.sendCommand('STOP');
        setActive(null);
      } else {
        await api.sendCommand(cmd, speed);
        setActive(cmd);
      }
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }, [speed]);

  // Keyboard control
  useEffect(() => {
    if (!isManual) return;

    const down = (e: KeyboardEvent) => {
      if (e.repeat) return;
      const dir = KEY_MAP[e.code];
      if (dir) {
        e.preventDefault();
        sendCmd(dir);
      }
    };
    const up = (e: KeyboardEvent) => {
      const dir = KEY_MAP[e.code];
      if (dir && dir === active) {
        sendCmd('STOP');
      }
    };

    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);
    return () => {
      window.removeEventListener('keydown', down);
      window.removeEventListener('keyup', up);
    };
  }, [isManual, active, sendCmd]);

  return (
    <div className="flex flex-col items-center gap-2">
      <p className="section-label">Directional Control</p>

      {!isManual && (
        <p className="text-xs text-warning/70 mb-1">Switch to MANUAL mode to control</p>
      )}

      {/* D-Pad grid */}
      <div className="grid grid-cols-3 gap-1.5 w-fit">
        {/* Row 1: blank, up, blank */}
        <div />
        <ControlButton
          id="btn-forward"
          direction="FORWARD"
          icon={<ArrowUp size={22} />}
          active={active === 'FORWARD'}
          disabled={!isManual}
          onPress={() => sendCmd('FORWARD')}
          onRelease={() => sendCmd('STOP')}
        />
        <div />

        {/* Row 2: left, stop, right */}
        <ControlButton
          id="btn-left"
          direction="LEFT"
          icon={<ArrowLeft size={22} />}
          active={active === 'LEFT'}
          disabled={!isManual}
          onPress={() => sendCmd('LEFT')}
          onRelease={() => sendCmd('STOP')}
        />
        <StopButton disabled={!isManual} onPress={() => sendCmd('STOP')} />
        <ControlButton
          id="btn-right"
          direction="RIGHT"
          icon={<ArrowRight size={22} />}
          active={active === 'RIGHT'}
          disabled={!isManual}
          onPress={() => sendCmd('RIGHT')}
          onRelease={() => sendCmd('STOP')}
        />

        {/* Row 3: blank, down, blank */}
        <div />
        <ControlButton
          id="btn-backward"
          direction="BACKWARD"
          icon={<ArrowDown size={22} />}
          active={active === 'BACKWARD'}
          disabled={!isManual}
          onPress={() => sendCmd('BACKWARD')}
          onRelease={() => sendCmd('STOP')}
        />
        <div />
      </div>

      <p className="text-xs text-muted mt-1">Arrow keys / WASD supported</p>

      {error && (
        <p className="text-xs text-danger mt-1">{error}</p>
      )}
    </div>
  );
}

function ControlButton({
  id, icon, active, disabled, onPress, onRelease,
}: {
  id: string;
  direction: string;
  icon: React.ReactNode;
  active: boolean;
  disabled: boolean;
  onPress: () => void;
  onRelease: () => void;
}) {
  return (
    <button
      id={id}
      className={clsx('control-key', active && 'active')}
      disabled={disabled}
      onMouseDown={onPress}
      onMouseUp={onRelease}
      onMouseLeave={onRelease}
      onTouchStart={(e) => { e.preventDefault(); onPress(); }}
      onTouchEnd={(e) => { e.preventDefault(); onRelease(); }}
    >
      {icon}
    </button>
  );
}

function StopButton({ disabled, onPress }: { disabled: boolean; onPress: () => void }) {
  return (
    <button
      id="btn-stop"
      className={clsx(
        'w-14 h-14 rounded-xl border border-muted/30 flex items-center justify-center',
        'text-muted hover:text-white hover:border-white/40 transition-all cursor-pointer',
        'active:scale-95',
        disabled && 'opacity-30 cursor-not-allowed'
      )}
      disabled={disabled}
      onClick={onPress}
    >
      <Square size={18} />
    </button>
  );
}
