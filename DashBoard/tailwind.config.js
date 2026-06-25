/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Robotics control panel color system
        panel:   { DEFAULT: '#0d1117', light: '#161b22', border: '#30363d' },
        accent:  { DEFAULT: '#00d4ff', dim: '#0097b8', glow: 'rgba(0,212,255,0.15)' },
        success: { DEFAULT: '#00ff88', dim: '#00b060' },
        warning: { DEFAULT: '#ffb800', dim: '#cc9200' },
        danger:  { DEFAULT: '#ff3b3b', dim: '#cc2020', glow: 'rgba(255,59,59,0.2)' },
        muted:   '#8b949e',
      },
      fontFamily: {
        sans:  ['Inter', 'system-ui', 'sans-serif'],
        mono:  ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'accent-glow': '0 0 20px rgba(0,212,255,0.3)',
        'danger-glow': '0 0 20px rgba(255,59,59,0.4)',
        'panel':       '0 4px 24px rgba(0,0,0,0.5)',
        'inset-glow':  'inset 0 1px 0 rgba(255,255,255,0.05)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow':  'spin 3s linear infinite',
        'blink':      'blink 1s step-end infinite',
      },
      keyframes: {
        blink: { '0%,100%': { opacity: 1 }, '50%': { opacity: 0 } },
      },
    },
  },
  plugins: [],
}
