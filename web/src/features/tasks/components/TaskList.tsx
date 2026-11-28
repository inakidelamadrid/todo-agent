import { Check, Globe, Home, type LucideIcon, Monitor, Phone, RotateCw, ShoppingBag } from 'lucide-react'
import type { ReactNode } from 'react'
import { flushSync } from 'react-dom'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { TaskGroup } from '../model/tasks'
import { taskRow } from '../model/taskRow'
import type { DateKey, Task, TaskContext } from '../model/types'

export interface TaskListProps {
  readonly status: 'loading' | 'error' | 'ready'
  readonly errorMessage?: string
  readonly groups: readonly TaskGroup[]
  readonly today: DateKey
  readonly busyIds?: ReadonlySet<string>
  readonly onComplete: (id: string) => void
  readonly onDrop: (id: string) => void
  readonly onRetry: () => void
}

const CONTEXT_ICON: Readonly<Record<TaskContext, LucideIcon>> = {
  home: Home,
  computer: Monitor,
  phone: Phone,
  errand: ShoppingBag,
  anywhere: Globe,
}

const prefersReducedMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false

/** Fade a removed row over 200ms (see `.task-row` in index.css); instant under reduced motion or without support. */
const withFade = (fn: () => void) => () => {
  if (!document.startViewTransition || prefersReducedMotion()) return fn()
  document.startViewTransition(() => flushSync(fn))
}

const Panel = ({ count, children, busy }: { readonly count?: number; readonly children: ReactNode; readonly busy?: boolean }) => (
  <section aria-labelledby="tasks-heading" aria-busy={busy || undefined} className="overflow-hidden rounded-xl border bg-card">
    <h2 id="tasks-heading" className="label-caps border-b px-4 py-3 text-xs text-muted-foreground md:px-6">
      Tasks{count !== undefined && <span className="tabular"> · {count}</span>}
    </h2>
    {children}
  </section>
)

const Bar = ({ className }: { readonly className?: string }) => (
  <div className={cn('animate-pulse rounded-md bg-muted motion-reduce:animate-none', className)} />
)

const Skeleton = () => (
  <Panel busy>
    <span className="sr-only">Loading tasks</span>
    {[0, 1, 2].map((i) => (
      <div key={i} className="flex items-center gap-4 border-t px-4 py-4 first:border-t-0 md:px-6">
        <Bar className="size-4 rounded-full" />
        <div className="flex flex-1 flex-col gap-2">
          <Bar className="h-4 w-48 max-w-full" />
          <Bar className="h-3 w-32" />
        </div>
        <Bar className="hidden h-8 w-36 md:block" />
      </div>
    ))}
  </Panel>
)

const Row = ({ task, today, busy, onComplete, onDrop }: {
  readonly task: Task
  readonly today: DateKey
  readonly busy: boolean
} & Pick<TaskListProps, 'onComplete' | 'onDrop'>) => {
  const row = taskRow(task, today)
  const Icon = CONTEXT_ICON[task.context]
  return (
    <li
      className={cn(
        'task-row grid grid-cols-[1rem_1fr] gap-x-3 gap-y-3 border-t px-4 py-3.5 transition-opacity duration-200 first:border-t-0 md:grid-cols-[1rem_1fr_auto] md:items-center md:px-6',
        busy && 'opacity-60',
      )}
      style={{ viewTransitionName: `task-${task.id}` }}
      aria-busy={busy || undefined}
    >
      <Icon className="mt-1 size-4 text-muted-foreground md:mt-0" role="img" aria-label={row.contextLabel} />
      <div className="min-w-0">
        <p className="font-semibold leading-snug break-words">{row.title}</p>
        {row.firstStep && <p className="mt-0.5 text-sm leading-relaxed text-muted-foreground">{row.firstStep}</p>}
        <p className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
          <span className="label-caps rounded-sm border px-1.5 py-px text-[0.7rem] text-muted-foreground">{row.sizeLabel}</span>
          {row.date && (
            <span className={cn('tabular', row.date.tone === 'muted' ? 'text-muted-foreground' : 'text-foreground')}>
              {row.date.text}
            </span>
          )}
        </p>
      </div>
      <div className="col-start-2 flex gap-2 md:col-start-3">
        <Button variant="outline" disabled={busy} onClick={withFade(() => onComplete(task.id))} className="max-md:h-11 max-md:flex-1">
          <Check aria-hidden="true" />
          Done
          <span className="sr-only">: {row.title}</span>
        </Button>
        <Button variant="ghost" disabled={busy} onClick={withFade(() => onDrop(task.id))} className="max-md:h-11 max-md:flex-1">
          Let go
          <span className="sr-only">: {row.title}</span>
        </Button>
      </div>
    </li>
  )
}

export const TaskList = ({ status, errorMessage, groups, today, busyIds, onComplete, onDrop, onRetry }: TaskListProps) => {
  if (status === 'loading') return <Skeleton />

  if (status === 'error') {
    return (
      <Panel>
        <div role="alert" className="flex flex-col items-start gap-4 px-4 py-8 md:flex-row md:items-center md:px-6">
          <p className="flex-1 leading-relaxed">
            Your tasks didn’t load.{' '}
            <span className="text-muted-foreground">{errorMessage ?? 'Check that the API is running, then try again.'}</span>
          </p>
          <Button variant="outline" onClick={onRetry} className="max-md:h-11">
            <RotateCw aria-hidden="true" />
            Try again
          </Button>
        </div>
      </Panel>
    )
  }

  const count = groups.reduce((n, g) => n + g.tasks.length, 0)

  if (count === 0) {
    return (
      <Panel count={0}>
        <p className="px-4 py-12 text-center leading-relaxed text-muted-foreground md:px-6">
          Nothing on your list. Capture something with <kbd className="rounded border px-1.5 font-mono text-sm text-foreground">/</kbd>.
        </p>
      </Panel>
    )
  }

  return (
    <Panel count={count}>
      {groups.map((group) => (
        <section key={group.key} aria-labelledby={`tasks-group-${group.key}`}>
          <h3 id={`tasks-group-${group.key}`} className="label-caps border-t bg-muted/50 px-4 py-2 text-xs text-muted-foreground md:px-6">
            {group.label} <span className="tabular">· {group.tasks.length}</span>
          </h3>
          <ul className="border-t">
            {group.tasks.map((task) => (
              <Row key={task.id} task={task} today={today} busy={busyIds?.has(task.id) ?? false} onComplete={onComplete} onDrop={onDrop} />
            ))}
          </ul>
        </section>
      ))}
    </Panel>
  )
}
