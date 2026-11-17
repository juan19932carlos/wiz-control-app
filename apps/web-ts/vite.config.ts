import path from 'node:path'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [tailwindcss(), svelte()],
  resolve: {
    alias: { $lib: path.resolve('./src/lib') },
  },
  server: {
    // The Python server owns /api. Proxying keeps the browser on one origin, so no CORS is needed.
    proxy: { '/api': process.env.WIZ_API_URL ?? 'http://127.0.0.1:8000' },
  },
})
