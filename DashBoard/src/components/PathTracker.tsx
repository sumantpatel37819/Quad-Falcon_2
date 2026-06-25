// src/components/PathTracker.tsx
// Canvas-based path visualization showing robot's local (x,y) trail
// Also supports GPS-based coordinates by normalizing to canvas space

import { useEffect, useRef } from 'react';
import { useRobotStore } from '../store/robotStore';
import { api } from '../services/api';
import { RotateCcw, MapPin } from 'lucide-react';
import type { Waypoint } from '../types/robot';

export function PathTracker() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { path, resetPath } = useRobotStore();

  // Redraw whenever path changes
  useEffect(() => {
    drawPath(canvasRef.current, path);
  }, [path]);

  const handleReset = async () => {
    await api.resetPath().catch(() => {});
    resetPath();
  };

  const waypointCount = path.length;
  const latest = path[path.length - 1];

  return (
    <div className="panel-card p-3 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MapPin size={13} className="text-accent" />
          <span className="section-label !mb-0">Path Trail</span>
          <span className="text-xs text-muted">({waypointCount} pts)</span>
        </div>
        <button id="btn-reset-path" onClick={handleReset} className="btn-ghost text-xs py-0.5 px-2">
          <RotateCcw size={11} />
          Reset
        </button>
      </div>

      {/* Canvas */}
      <div className="relative bg-panel rounded-lg overflow-hidden" style={{ height: 160 }}>
        <canvas
          ref={canvasRef}
          id="path-canvas"
          className="w-full h-full"
          width={400}
          height={160}
        />
        {path.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-xs text-muted">
            No path recorded yet
          </div>
        )}
      </div>

      {/* Latest position */}
      {latest && (
        <div className="flex gap-4 text-xs text-muted">
          <span>X: <span className="text-white font-mono">{latest.local_x.toFixed(2)}m</span></span>
          <span>Y: <span className="text-white font-mono">{latest.local_y.toFixed(2)}m</span></span>
          {latest.gps_ok && (
            <span className="ml-auto text-success">GPS</span>
          )}
        </div>
      )}
    </div>
  );
}

function drawPath(canvas: HTMLCanvasElement | null, path: Waypoint[]) {
  if (!canvas || path.length === 0) {
    if (canvas) {
      const ctx = canvas.getContext('2d')!;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    return;
  }

  const ctx = canvas.getContext('2d')!;
  const W = canvas.width;
  const H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  // ── Draw grid ──────────────────────────────────────────────────────────
  ctx.strokeStyle = 'rgba(48,54,61,0.6)';
  ctx.lineWidth = 0.5;
  for (let x = 0; x <= W; x += 40) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
  }
  for (let y = 0; y <= H; y += 40) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
  }

  // ── Normalize coordinates to canvas ───────────────────────────────────
  const xs = path.map(w => w.local_x);
  const ys = path.map(w => w.local_y);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const rangeX = Math.max(maxX - minX, 1);
  const rangeY = Math.max(maxY - minY, 1);
  const padding = 20;

  const toCanvas = (wx: number, wy: number) => ({
    cx: padding + ((wx - minX) / rangeX) * (W - 2 * padding),
    cy: H - padding - ((wy - minY) / rangeY) * (H - 2 * padding),
  });

  // ── Draw path line ─────────────────────────────────────────────────────
  const gradient = ctx.createLinearGradient(0, 0, W, H);
  gradient.addColorStop(0, 'rgba(0,180,210,0.4)');
  gradient.addColorStop(1, 'rgba(0,212,255,0.9)');

  ctx.beginPath();
  ctx.strokeStyle = gradient;
  ctx.lineWidth = 2;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  path.forEach((wp, i) => {
    const { cx, cy } = toCanvas(wp.local_x, wp.local_y);
    i === 0 ? ctx.moveTo(cx, cy) : ctx.lineTo(cx, cy);
  });
  ctx.stroke();

  // ── Draw Home marker ──────────────────────────────────────────────────
  if (path.length > 0) {
    const home = path[0];
    const { cx, cy } = toCanvas(home.local_x, home.local_y);
    ctx.beginPath();
    ctx.arc(cx, cy, 5, 0, Math.PI * 2);
    ctx.fillStyle = '#00ff88';
    ctx.fill();
    ctx.fillStyle = '#00ff88';
    ctx.font = '9px JetBrains Mono';
    ctx.fillText('HOME', cx + 7, cy + 3);
  }

  // ── Draw current position marker ──────────────────────────────────────
  const curr = path[path.length - 1];
  const { cx, cy } = toCanvas(curr.local_x, curr.local_y);

  // Glow ring
  const grd = ctx.createRadialGradient(cx, cy, 0, cx, cy, 14);
  grd.addColorStop(0, 'rgba(0,212,255,0.5)');
  grd.addColorStop(1, 'rgba(0,212,255,0)');
  ctx.beginPath();
  ctx.arc(cx, cy, 14, 0, Math.PI * 2);
  ctx.fillStyle = grd;
  ctx.fill();

  ctx.beginPath();
  ctx.arc(cx, cy, 5, 0, Math.PI * 2);
  ctx.fillStyle = '#00d4ff';
  ctx.fill();
}
