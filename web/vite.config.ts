/// <reference types="vitest/config" />
import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv, type ProxyOptions } from 'vite'

/** Dev proxy: the browser calls same-origin `/api/*`; the proxy only forwards it to the API. */
export const apiProxy = (env: Record<string, string>): Record<string, ProxyOptions> => ({
  '/api': {
    target: env.API_URL?.trim() || 'http://127.0.0.1:8000',
    changeOrigin: true,
    rewrite: (p) => p.replace(/^\/api/, ''),
  },
})

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, import.meta.dirname, '')
  const needsProxy = command === 'serve' && mode !== 'test'
  return {
    plugins: [react(), tailwindcss()],
    resolve: { alias: { '@': path.resolve(import.meta.dirname, './src') } },
    server: needsProxy ? { proxy: apiProxy(env) } : undefined,
    test: { environment: 'node' },
  }
})
