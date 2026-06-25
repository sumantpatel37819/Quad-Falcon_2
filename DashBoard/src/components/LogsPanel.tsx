// src/components/LogsPanel.tsx
// Live timestamped command/event log display

import { useRef, useEffect } from 'react';
import { useRobotStore } from '../store/robotStore';
import { Terminal, Trash2 } from 'lucide-react';
import clsx from 'clsx';
import type { LogLevel } from '../types/robot';

const LEVEL_COLORS: Record<LogLevel, string> = {
  DEBUG:    'text-muted',
  INFO:     'text-accent',
  WARN:     'text-warning',
  ERROR:    'text-danger',
  CRITICAL: 'text-danger font-bold',
};

export function LogsPanel() {
  const { logs, clearLogs } = useRobotStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new logs
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, [logs]);

  return (
    <div className="panel-card flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 border-b border-panel-border shrink-0">
        <div className="flex items-center gap-2">
          <Terminal size={13} className="text-accent" />
          <span className="text-xs font-semibold uppercase tracking-wider text-muted">System Logs</span>
          <span className="text-xs text-muted">({logs.length})</span>
        </div>
        <button
          id="btn-clear-logs"
          onClick={clearLogs}
          className="text-muted hover:text-white transition-colors"
          title="Clear logs"
        >
          <Trash2 size={13} />
        </button>
      </div>

      <div
        id="logs-container"
        className="flex-1 overflow-y-auto p-2 space-y-0.5 font-mono text-xs"
        style={{ minHeight: 0 }}
      >
        {logs.length === 0 ? (
          <p className="text-muted text-center pt-4">No logs yet</p>
        ) : (
          logs.map((entry, i) => (
            <div key={i} className="flex gap-2 hover:bg-panel-border/20 px-1 py-0.5 rounded">
              <span className="text-muted shrink-0 w-20">
                {new Date(entry.ts).toLocaleTimeString()}
              </span>
              <span
                className={clsx(
                  'w-14 shrink-0 uppercase',
                  LEVEL_COLORS[entry.level] ?? 'text-muted'
                )}
              >
                [{entry.level}]
              </span>
              <span className="text-muted shrink-0">{entry.module}:</span>
              <span className="text-white/80 break-all">{entry.msg}</span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
