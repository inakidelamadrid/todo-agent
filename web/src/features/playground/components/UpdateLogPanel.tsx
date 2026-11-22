import { AlertTriangle, Check, CircleDashed, CloudOff, FlaskConical, Inbox, RotateCw, Search } from 'lucide-react'
import type { ComponentType, ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { cn } from '@/lib/utils'
import { formatReceivedAt, statusTone, type Tone, type UpdateLogFilters, type UpdateLogItem, type UpdateStatus } from '../updateLog'

export type UpdateLogStatus = 'loading' | 'ready' | 'error'

interface Props {
  readonly items: readonly UpdateLogItem[]
  readonly status: UpdateLogStatus
  readonly error?: string
  readonly filters: UpdateLogFilters
  readonly onFiltersChange: (filters: UpdateLogFilters) => void
  readonly onRefresh: () => void
  /** Injected so times are testable and stable within one render. */
  readonly now: Date
}

const STATUS_OPTIONS: readonly { readonly value: UpdateLogFilters['status']; readonly label: string }[] = [
  { value: 'all', label: 'All statuses' },
  { value: 'received', label: 'Received' },
  { value: 'processed', label: 'Processed' },
  { value: 'failed', label: 'Failed' },
]

const STATUS_LABEL: Readonly<Record<UpdateStatus, string>> = { received: 'Received', processed: 'Processed', failed: 'Failed' }

const TONE_STYLE: Readonly<Record<Tone, { readonly icon: ComponentType<{ className?: string }>; readonly className: string }>> = {
  neutral: { icon: CircleDashed, className: 'text-muted-foreground' },
  good: { icon: Check, className: 'text-paid' },
  bad: { icon: AlertTriangle, className: 'text-overdue' },
}

const StatusTag = ({ status }: { readonly status: UpdateStatus }) => {
  const { icon: Icon, className } = TONE_STYLE[statusTone(status)]
  return (
    <span className={cn('inline-flex items-center gap-1.5 text-sm font-medium whitespace-nowrap', className)}>
      <Icon className="size-4 shrink-0" aria-hidden="true" />
      {STATUS_LABEL[status]}
    </span>
  )
}

const PlaygroundTag = () => (
  <span className="label-caps inline-flex items-center gap-1 rounded-sm border border-line-telecom/40 px-1.5 py-px text-[0.6875rem] text-line-telecom">
    <FlaskConical className="size-3" aria-hidden="true" />
    Playground
  </span>
)

const Route = ({ route }: { readonly route: string }) => (
  <code className="truncate font-mono text-[0.8125rem]">{route}</code>
)

const Bar = ({ className }: { readonly className?: string }) => (
  <div className={cn('animate-pulse rounded-md bg-muted motion-reduce:animate-none', className)} />
)

const SkeletonRows = () => (
  <div role="status" aria-label="Loading updates">
    {[0, 1, 2, 3, 4].map((i) => (
      <div key={i} className="flex items-center gap-4 border-t px-4 py-3.5 first:border-t-0 md:px-6">
        <Bar className="h-4 w-20" />
        <Bar className="hidden h-4 w-16 md:block" />
        <Bar className="h-4 flex-1 md:max-w-56" />
        <Bar className="h-4 w-24" />
      </div>
    ))}
  </div>
)

const Message = ({ icon: Icon, tone, title, body, action }: {
  readonly icon: ComponentType<{ className?: string }>
  readonly tone: 'muted' | 'bad'
  readonly title: string
  readonly body: string
  readonly action?: ReactNode
}) => (
  <div role={tone === 'bad' ? 'alert' : undefined} className="flex flex-col items-center gap-3 px-4 py-12 text-center md:px-6">
    <span
      className={cn(
        'grid size-11 place-items-center rounded-full border',
        tone === 'bad' ? 'border-overdue/60 text-overdue' : 'border-input text-muted-foreground',
      )}
    >
      <Icon className="size-5" aria-hidden="true" />
    </span>
    <div>
      <p className="font-heading text-xl font-semibold">{title}</p>
      <p className="mx-auto mt-1 max-w-[48ch] text-muted-foreground">{body}</p>
    </div>
    {action}
  </div>
)

const HEAD = 'label-caps px-4 py-3 text-xs font-semibold text-muted-foreground'

const Rows = ({ items, now }: { readonly items: readonly UpdateLogItem[]; readonly now: Date }) => (
  <>
    {/* Desktop: table */}
    <table className="hidden w-full text-left md:table">
      <caption className="sr-only">Recent Telegram updates</caption>
      <thead>
        <tr className="border-b">
          <th scope="col" className={cn(HEAD, 'pl-6')}>Received</th>
          <th scope="col" className={HEAD}>Kind</th>
          <th scope="col" className={HEAD}>Route</th>
          <th scope="col" className={cn(HEAD, 'pr-6')}>Status</th>
        </tr>
      </thead>
      <tbody>
        {items.map((item) => (
          <tr key={item.updateId} className="border-t transition-colors duration-200 first:border-t-0 hover:bg-muted/40">
            <td className="py-3 pr-4 pl-6 whitespace-nowrap tabular">
              <time dateTime={item.receivedAt} title={item.receivedAt}>{formatReceivedAt(item.receivedAt, now)}</time>
            </td>
            <td className="px-4 py-3 capitalize">{item.kind}</td>
            <td className="max-w-0 px-4 py-3 w-[45%]">
              <div className="flex min-w-0 items-center gap-2">
                <Route route={item.route} />
                {item.playground && <PlaygroundTag />}
              </div>
            </td>
            <td className="py-3 pr-6 pl-4"><StatusTag status={item.status} /></td>
          </tr>
        ))}
      </tbody>
    </table>

    {/* Mobile: stacked rows */}
    <ul className="md:hidden" aria-label="Recent Telegram updates">
      {items.map((item) => (
        <li key={item.updateId} className="flex flex-col gap-1.5 border-t px-4 py-3 first:border-t-0">
          <div className="flex min-w-0 items-center justify-between gap-3">
            <Route route={item.route} />
            <StatusTag status={item.status} />
          </div>
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted-foreground">
            <span className="capitalize">{item.kind}</span>
            <span aria-hidden="true">·</span>
            <time className="tabular" dateTime={item.receivedAt}>{formatReceivedAt(item.receivedAt, now)}</time>
            {item.playground && <PlaygroundTag />}
          </div>
        </li>
      ))}
    </ul>
  </>
)

/** Presentational: everything comes in as props, and nothing here fetches or stores. */
export const UpdateLogPanel = ({ items, status, error, filters, onFiltersChange, onRefresh, now }: Props) => {
  const loading = status === 'loading'
  const filtered = filters.status !== 'all' || filters.route.trim() !== ''
  return (
    <section aria-labelledby="update-log-title" className="overflow-hidden rounded-xl border bg-card">
      <div className="flex flex-wrap items-center gap-3 border-b px-4 py-3 md:px-6">
        <h2 id="update-log-title" className="label-caps mr-auto text-sm">
          Recent updates{status === 'ready' && <span className="text-muted-foreground"> · {items.length}</span>}
        </h2>
        <div className="flex w-full flex-wrap items-center gap-2 sm:w-auto">
          <Select
            value={filters.status}
            onValueChange={(v) => v && onFiltersChange({ ...filters, status: v as UpdateLogFilters['status'] })}
            items={STATUS_OPTIONS}
            disabled={loading}
          >
            <SelectTrigger aria-label="Filter by status" className="w-36"><SelectValue /></SelectTrigger>
            <SelectContent>
              {STATUS_OPTIONS.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
            </SelectContent>
          </Select>
          <div className="relative min-w-0 flex-1 sm:w-48 sm:flex-none">
            <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
            <Input
              aria-label="Filter by route"
              placeholder="Route"
              value={filters.route}
              disabled={loading}
              onChange={(e) => onFiltersChange({ ...filters, route: e.target.value })}
              className="pl-8 font-mono"
            />
          </div>
          <Button variant="outline" disabled={loading} onClick={onRefresh} aria-label="Refresh updates">
            <RotateCw className={cn(loading && 'animate-spin motion-reduce:animate-none')} aria-hidden="true" />
            <span className="hidden sm:inline">Refresh</span>
          </Button>
        </div>
      </div>

      {loading && <SkeletonRows />}
      {status === 'error' && (
        <Message
          icon={CloudOff}
          tone="bad"
          title="Can’t load updates"
          body={error ?? 'Check that the API is running, then try again.'}
          action={
            <Button variant="outline" onClick={onRefresh}>
              <RotateCw aria-hidden="true" />
              Try again
            </Button>
          }
        />
      )}
      {status === 'ready' && items.length === 0 && (
        filtered ? (
          <Message icon={Search} tone="muted" title="Nothing matches" body="No updates match these filters. Try another status or route." />
        ) : (
          <Message icon={Inbox} tone="muted" title="No updates yet" body="Send your dev bot a message." />
        )
      )}
      {status === 'ready' && items.length > 0 && <Rows items={items} now={now} />}
    </section>
  )
}
