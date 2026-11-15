import { CloudOff, DownloadCloud, KeyRound, RotateCw } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { LoadError } from '../store/useBillsStore'

const Bar = ({ className }: { readonly className?: string }) => (
  <div className={cn('animate-pulse rounded-md bg-muted motion-reduce:animate-none', className)} />
)

/** Skeleton in the shape of the strip, the network panel and the table: no spinner in content. */
export const BillsSkeleton = () => (
  <div className="flex flex-col gap-5" aria-busy="true" aria-label="Loading bills">
    <div className="grid divide-y divide-border rounded-xl border bg-card md:grid-cols-2 md:divide-x md:divide-y-0">
      {[0, 1].map((i) => (
        <div key={i} className="flex flex-col gap-3 px-5 py-4 md:px-6">
          <Bar className="h-3.5 w-32" />
          <Bar className="h-9 w-44" />
          <Bar className="h-1.5 w-full rounded-full" />
        </div>
      ))}
    </div>
    <div className="rounded-xl border bg-card">
      <div className="flex gap-3 border-b px-4 py-3 md:px-6">
        {[0, 1, 2, 3].map((i) => <Bar key={i} className="h-7 w-28" />)}
      </div>
      <div className="flex flex-col gap-10 px-6 py-10">
        {[0, 1, 2, 3].map((i) => <Bar key={i} className="h-2 w-full rounded-full" />)}
      </div>
    </div>
    <div className="overflow-hidden rounded-xl border bg-card">
      {[0, 1, 2, 3, 4].map((i) => (
        <div key={i} className="flex items-center gap-4 border-t px-6 py-4 first:border-t-0">
          <Bar className="h-1 w-5 rounded-full" />
          <div className="flex flex-1 flex-col gap-2">
            <Bar className="h-4 w-40" />
            <Bar className="h-3 w-24" />
          </div>
          <Bar className="h-4 w-24" />
          <Bar className="h-8 w-24" />
        </div>
      ))}
    </div>
  </div>
)

const copyFor = (error: LoadError) =>
  error.status === 401
    ? {
        icon: KeyRound,
        title: 'The API rejected the key',
        body: 'Set API_KEY in web/.env.local to one of the keys in api/.env (API_KEYS), then restart make web-dev.',
      }
    : error.status === 0 || error.status >= 500
      ? {
          icon: CloudOff,
          title: 'Can’t reach the bills API',
          body: 'Check that the API is running (make api-dev) and that the database is up (make db-up).',
        }
      : { icon: CloudOff, title: 'Couldn’t load your bills', body: error.message }

export const LoadErrorPanel = ({ error, onRetry }: { readonly error: LoadError; readonly onRetry: () => void }) => {
  const { icon: Icon, title, body } = copyFor(error)
  return (
    <section role="alert" className="flex flex-col items-start gap-4 rounded-xl border bg-card px-6 py-8 md:flex-row md:items-center">
      <span className="grid size-11 shrink-0 place-items-center rounded-full border border-overdue/60 text-overdue">
        <Icon className="size-5" aria-hidden="true" />
      </span>
      <div className="flex-1">
        <h2 className="font-heading text-xl font-semibold">{title}</h2>
        <p className="mt-1 max-w-[60ch] text-muted-foreground">{body}</p>
      </div>
      <Button variant="outline" onClick={onRetry}>
        <RotateCw aria-hidden="true" />
        Retry
      </Button>
    </section>
  )
}

interface ImportBannerProps {
  readonly count: number
  readonly onImport: () => Promise<void>
  readonly onDiscard: () => void
}

/** Quiet inline offer to move pre-API browser data into the API. Never automatic. */
export const ImportBanner = ({ count, onImport, onDiscard }: ImportBannerProps) => {
  const [busy, setBusy] = useState(false)
  return (
    <section className="flex flex-col gap-3 rounded-xl border bg-card px-5 py-4 md:flex-row md:items-center md:px-6">
      <DownloadCloud className="size-5 shrink-0 text-line-telecom" aria-hidden="true" />
      <p className="flex-1">
        <span className="font-semibold">
          Import {count} {count === 1 ? 'bill' : 'bills'} saved in this browser?
        </span>{' '}
        <span className="text-muted-foreground">They were saved before the app used the API.</span>
      </p>
      <div className="flex gap-2">
        <Button variant="ghost" disabled={busy} onClick={onDiscard}>
          Discard
        </Button>
        <Button
          disabled={busy}
          onClick={async () => {
            setBusy(true)
            await onImport().finally(() => setBusy(false))
          }}
        >
          {busy ? 'Importing…' : 'Import'}
        </Button>
      </div>
    </section>
  )
}
