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
    // Reachable from the whole LAN, for example http://home-lab.lan:5173. The API stays on localhost.
    host: true,
    // Vite rejects unknown Host headers. '.lan' allows every *.lan name on the local network.
    allowedHosts: ['.lan'],
    // The Python server owns /api. Proxying keeps the browser on one origin, so no CORS is needed.
    proxy: { '/api': process.env.WIZ_API_URL ?? 'http://127.0.0.1:8000' },
  },
})
