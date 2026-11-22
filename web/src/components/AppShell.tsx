import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

export interface NavItem {
  readonly href: string
  readonly label: string
  readonly icon: ReactNode
  readonly current: boolean
}

export const BrandMark = () => (
  <svg viewBox="0 0 32 32" className="size-8" aria-hidden="true">
    <path d="M2 10h11l6 6h11" stroke="var(--line-streaming)" strokeWidth="3" fill="none" strokeLinecap="round" />
    <path d="M2 16h28" stroke="var(--line-telecom)" strokeWidth="3" fill="none" strokeLinecap="round" />
    <path d="M2 22h11l6-6" stroke="var(--line-utilities)" strokeWidth="3" fill="none" strokeLinecap="round" />
    <circle cx="16" cy="16" r="5.5" fill="var(--rail)" stroke="var(--rail-foreground)" strokeWidth="2.5" />
  </svg>
)

export const AppShell = ({
  children,
  items,
  status,
  account,
}: {
  readonly children: ReactNode
  readonly items: readonly NavItem[]
  readonly status?: ReactNode
  readonly account?: ReactNode
}) => (
  <div className="min-h-dvh md:grid md:grid-cols-[15rem_1fr]">
    <aside className="flex items-center gap-6 bg-rail px-4 py-3 text-rail-foreground md:sticky md:top-0 md:h-dvh md:flex-col md:items-stretch md:gap-8 md:px-5 md:py-7">
      <div className="flex shrink-0 items-center gap-2.5">
        <BrandMark />
        {/* The mark alone on the narrowest phones, so two nav entries and the account still fit. */}
        <span className="label-caps text-lg tracking-[0.06em] max-[419px]:sr-only">todo-agent</span>
      </div>
      <nav aria-label="Main" className="flex min-w-0 flex-1 gap-1 md:flex-col">
        {items.map((item) => (
          <a
            key={item.href}
            href={item.href}
            aria-current={item.current ? 'page' : undefined}
            className={cn(
              'relative flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium outline-none transition-colors duration-200 focus-visible:ring-2 focus-visible:ring-ring',
              item.current ? 'bg-white/8' : 'text-[#C3CDE8] hover:bg-white/5 hover:text-rail-foreground',
            )}
          >
            {item.icon}
            {item.label}
            {item.current && <span className="absolute inset-x-3 -bottom-px hidden h-0.5 rounded bg-line-streaming md:block" />}
          </a>
        ))}
      </nav>
      <div className="hidden flex-col gap-6 md:flex">
        {status}
        <p className="text-xs leading-relaxed text-[#A9B6DA]">
          Saved to your bills API.
        </p>
      </div>
      {account}
    </aside>
    <main id="bills" className="min-w-0">
      {children}
    </main>
  </div>
)
