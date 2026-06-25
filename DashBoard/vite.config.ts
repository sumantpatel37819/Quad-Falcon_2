import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Proxy API calls to Raspberry Pi backend
      // Change PI_IP to your Pi's IP address or hostname
      '/control': {
        target: 'http://raspberrypi.local:8000',
        changeOrigin: true,
      },
      '/video': {
        target: 'http://raspberrypi.local:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://raspberrypi.local:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://raspberrypi.local:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})
