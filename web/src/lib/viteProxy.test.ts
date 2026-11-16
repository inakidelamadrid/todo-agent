import { describe, expect, it } from 'vitest'
import { apiProxy } from '../../vite.config'

describe('apiProxy', () => {
  it('sets no API key header', () => {
    expect(apiProxy({ API_URL: 'http://api.test:9000', API_KEY: 'secret' })['/api']).not.toHaveProperty('headers')
  })

  it('does not need API_KEY', () => {
    expect(() => apiProxy({})).not.toThrow()
  })

  it('rewrites the /api prefix and targets API_URL', () => {
    const proxy = apiProxy({ API_URL: ' http://api.test:9000 ' })['/api']
    expect(proxy.target).toBe('http://api.test:9000')
    expect(proxy.changeOrigin).toBe(true)
    expect(proxy.rewrite?.('/api/bills?x=1')).toBe('/bills?x=1')
    expect(apiProxy({})['/api'].target).toBe('http://127.0.0.1:8000')
  })
})
