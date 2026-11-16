import { describe, expect, it } from 'vitest'
import { clerkAppearance } from './clerkAppearance'

describe('clerkAppearance', () => {
  it('uses only token references for colours', () => {
    const colours = Object.entries(clerkAppearance.variables).filter(([name]) => name.startsWith('color'))
    expect(colours.length).toBeGreaterThan(0)
    colours.forEach(([, value]) => expect(value).toMatch(/^var\(--[a-z-]+\)$/))
    expect(JSON.stringify(clerkAppearance)).not.toMatch(/#[0-9a-f]{3,8}\b|rgb\(|hsl\(/i)
  })

  it('hides the footer link', () => {
    expect(clerkAppearance.elements.footer).toEqual({ display: 'none' })
  })
})
