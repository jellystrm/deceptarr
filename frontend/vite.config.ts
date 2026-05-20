import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const BACKEND = 'http://localhost:8765'

export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: '../dist',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': BACKEND,
      '/torznab': BACKEND,
      '/grab': BACKEND,
      '/save': BACKEND,
      '/test': BACKEND,
      '/tasks': BACKEND,
    },
  },
})
