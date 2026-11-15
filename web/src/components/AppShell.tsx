import { ReceiptText } from 'lucide-react'
import type { ReactNode } from 'react'

const BrandMark = () => (
  <svg viewBox="0 0 32 32" className="size-8" aria-hidden="true">
    <path d="M2 10h11l6 6h11" stroke="var(--line-streaming)" strokeWidth="3" fill="none" strokeLinecap="round" />
    <path d="M2 16h28" stroke="var(--line-telecom)" strokeWidth="3" fill="none" strokeLinecap="round" />
    <path d="M2 22h11l6-6" stroke="var(--line-utilities)" strokeWidth="3" fill="none" strokeLinecap="round" />
    <circle cx="16" cy="16" r="5.5" fill="var(--rail)" stroke="var(--rail-foreground)" strokeWidth="2.5" />
  </svg>
)

export const AppShell = ({ children, status }: { readonly children: ReactNode; readonly status?: ReactNode }) => (
  <div className="min-h-dvh md:grid md:grid-cols-[15rem_1fr]">
    <aside className="flex items-center gap-6 bg-rail px-4 py-3 text-rail-foreground md:sticky md:top-0 md:h-dvh md:flex-col md:items-stretch md:gap-8 md:px-5 md:py-7">
      <div className="flex items-center gap-2.5">
        <BrandMark />
        <span className="label-caps text-lg tracking-[0.06em]">todo-agent</span>
      </div>
      <nav aria-label="Main" className="flex-1">
        <a
          href="#bills"
          aria-current="page"
          className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium bg-white/8 outline-none focus-visible:ring-2 focus-visible:ring-ring md:relative"
        >
          <ReceiptText className="size-4" aria-hidden="true" />
          Bills
          <span className="absolute inset-x-3 -bottom-px hidden h-0.5 rounded bg-line-streaming md:block" />
        </a>
      </nav>
      <div className="hidden flex-col gap-6 md:flex">
        {status}
        <p className="text-xs leading-relaxed text-[#A9B6DA]">
          Saved to your bills API.
        </p>
      </div>
    </aside>
    <main id="bills" className="min-w-0">
      {children}
    </main>
  </div>
)
