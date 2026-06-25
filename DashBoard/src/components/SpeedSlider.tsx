// src/components/SpeedSlider.tsx
// Motor speed control slider (0–255)

import { useRobotStore } from '../store/robotStore';
import { api } from '../services/api';
import { Gauge } from 'lucide-react';

export function SpeedSlider() {
  const { speed, setSpeed } = useRobotStore();

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const newSpeed = Number(e.target.value);
    setSpeed(newSpeed);
    try {
      await api.setSpeed(newSpeed);
    } catch {
      // Non-critical — speed will be applied with next command
    }
  };

  const pct = Math.round((speed / 255) * 100);

  return (
    <div className="space-y-2">
      <p className="section-label">Motor Speed</p>

      <div className="flex items-center gap-3">
        <Gauge size={16} className="text-accent shrink-0" />
        <div className="flex-1 relative">
          {/* Track */}
          <div className="h-2 bg-panel rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-accent/60 to-accent rounded-full transition-all"
              style={{ width: `${pct}%` }}
            />
          </div>
          {/* Slider input */}
          <input
            id="speed-slider"
            type="range"
            min={0}
            max={255}
            step={5}
            value={speed}
            onChange={handleChange}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
        </div>
        <span className="font-mono text-sm text-accent w-12 text-right">{speed}</span>
      </div>

      <div className="flex justify-between text-xs text-muted">
        <span>0</span>
        <span>{pct}%</span>
        <span>255</span>
      </div>

      {/* Quick presets */}
      <div className="flex gap-1.5 mt-1">
        {[80, 130, 180, 220].map((v) => (
          <button
            key={v}
            id={`speed-preset-${v}`}
            onClick={() => { setSpeed(v); api.setSpeed(v).catch(() => {}); }}
            className={`flex-1 py-1 rounded text-xs border transition-all
              ${speed === v
                ? 'border-accent/60 text-accent bg-accent/10'
                : 'border-panel-border text-muted hover:border-accent/30 hover:text-white'
              }`}
          >
            {v}
          </button>
        ))}
      </div>
    </div>
  );
}
