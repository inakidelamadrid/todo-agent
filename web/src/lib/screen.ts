import { type ReactNode, useSyncExternalStore } from 'react'
import type { NavItem } from '@/components/AppShell'

export interface ScreenDef {
  readonly id: string
  readonly label: string
  readonly icon: ReactNode
  readonly adminOnly?: boolean
  /** Reached only by typing `#<id>` on the dev server; never in the nav. */
  readonly devOnly?: boolean
  readonly render: () => ReactNode
}

export interface ScreenContext {
  readonly isAdmin: boolean
  readonly isDev: boolean
}

const isVisible = (def: ScreenDef, ctx: ScreenContext): boolean =>
  (!def.adminOnly || ctx.isAdmin) && (!def.devOnly || ctx.isDev)

/** Pure: the hash's screen if this user may see it, else the first (default) screen. */
export const resolveScreen = (hash: string, defs: readonly ScreenDef[], ctx: ScreenContext): ScreenDef =>
  defs.find((def) => hash === `#${def.id}` && isVisible(def, ctx)) ?? defs[0]

/** Pure: nav entries this user may see; dev-only screens never appear. */
export const visibleNav = (defs: readonly ScreenDef[], ctx: ScreenContext, current: string): readonly NavItem[] =>
  defs
    .filter((def) => !def.devOnly && isVisible(def, ctx))
    .map((def) => ({ href: `#${def.id}`, label: def.label, icon: def.icon, current: def.id === current }))

const subscribe = (onChange: () => void) => {
  window.addEventListener('hashchange', onChange)
  return () => window.removeEventListener('hashchange', onChange)
}

const readHash = () => window.location.hash

/** The one side effect: follow `hashchange`, so links and Back/Forward switch screens. */
export const useHashScreen = (defs: readonly ScreenDef[], ctx: ScreenContext): ScreenDef =>
  resolveScreen(useSyncExternalStore(subscribe, readHash), defs, ctx)
