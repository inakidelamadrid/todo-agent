/// <reference types="vitest/config" />
import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv, type ProxyOptions } from 'vite'

const PLACEHOLDER = 'change-me'

/**
 * Dev proxy: the browser calls same-origin `/api/*`; the proxy forwards to the
 * API and adds `X-API-Key` server-side, so the key never reaches client code.
 * `API_KEY` is deliberately not `VITE_`-prefixed and is read only here.
 */
const apiProxy = (env: Record<string, string>): Record<string, ProxyOptions> => {
  const key = env.API_KEY?.trim()
  if (!key) {
    throw new Error(
      'API_KEY is missing. Copy web/.env.example to web/.env.local and set API_KEY to one of the keys in api/.env (API_KEYS).',
    )
  }
  if (key === PLACEHOLDER) {
    console.warn('\n⚠ API_KEY is the placeholder "change-me". Fine for local dev only if api/.env uses it too; change both before sharing.\n')
  }
  return {
    '/api': {
      target: env.API_URL?.trim() || 'http://127.0.0.1:8000',
      changeOrigin: true,
      rewrite: (p) => p.replace(/^\/api/, ''),
      headers: { 'X-API-Key': key },
    },
  }
}

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
