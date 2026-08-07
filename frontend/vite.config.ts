import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/health': 'http://localhost:8000',
      '/system': 'http://localhost:8000',
      '/config': 'http://localhost:8000',
      '/mcp': 'http://localhost:8000',
      '/library': 'http://localhost:8000',
      '/projects': 'http://localhost:8000',
      '/telemetry': 'http://localhost:8000',
      '/packages': 'http://localhost:8000',
      '/activity': { target: 'http://localhost:8000', ws: true },
    },
  },
})
