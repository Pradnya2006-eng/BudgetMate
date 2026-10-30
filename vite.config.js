import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The Flask backend runs on port 5000 (see backend/app.py). While developing,
// Vite forwards every "/api/..." request there, so the browser only ever talks
// to one address and no CORS setup is needed.
const api = {
  '/api': { target: 'http://127.0.0.1:5000', changeOrigin: false },
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: { proxy: api },
  preview: { proxy: api },
})
