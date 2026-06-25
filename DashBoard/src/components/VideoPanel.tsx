// src/components/VideoPanel.tsx
// Live MJPEG camera stream from Raspberry Pi camera
// Uses <img> tag with MJPEG URL — compatible with all browsers, no WebRTC needed.

import { useState } from 'react';
import { Camera, CameraOff, Maximize2 } from 'lucide-react';
import { api } from '../services/api';
import { useRobotStore } from '../store/robotStore';
import clsx from 'clsx';

export function VideoPanel() {
  const { cameraOk } = useRobotStore();
  const [streamError, setStreamError] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);

  const streamUrl = api.videoStreamUrl();

  return (
    <div className={clsx(
      'panel-card flex flex-col overflow-hidden h-full',
      fullscreen && 'fixed inset-2 z-50'
    )}>
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-panel-border">
        <div className="flex items-center gap-2">
          {cameraOk && !streamError
            ? <Camera size={14} className="text-success" />
            : <CameraOff size={14} className="text-danger" />
          }
          <span className="text-xs font-medium text-muted uppercase tracking-wider">
            Live Camera Feed
          </span>
          {cameraOk && !streamError && (
            <span className="w-1.5 h-1.5 rounded-full bg-danger animate-blink ml-1" />
          )}
        </div>
        <button
          onClick={() => setFullscreen(f => !f)}
          className="text-muted hover:text-white transition-colors"
        >
          <Maximize2 size={14} />
        </button>
      </div>

      {/* Video area */}
      <div className="flex-1 relative bg-black flex items-center justify-center min-h-0">
        {streamError || !cameraOk ? (
          <div className="flex flex-col items-center gap-3 text-muted">
            <CameraOff size={48} className="opacity-30" />
            <p className="text-sm">Camera unavailable</p>
            <button
              className="btn-ghost text-xs py-1 px-3"
              onClick={() => setStreamError(false)}
            >
              Retry
            </button>
          </div>
        ) : (
          <img
            id="camera-stream"
            src={streamUrl}
            alt="Robot camera feed"
            className="w-full h-full object-contain"
            onError={() => setStreamError(true)}
            onLoad={() => setStreamError(false)}
          />
        )}

        {/* Overlay: scan line effect for aesthetics */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px)',
          }}
        />
      </div>

      {/* Footer status */}
      <div className="flex items-center justify-between px-3 py-1.5 border-t border-panel-border text-xs text-muted">
        <span className="font-mono">{streamUrl}</span>
        <span>{cameraOk ? '640×480 @ 15fps' : 'Offline'}</span>
      </div>
    </div>
  );
}
