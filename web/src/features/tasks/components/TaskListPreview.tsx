import { useState } from 'react'
import { toDateKey } from '@/features/bills/model/schedule'
import { cn } from '@/lib/utils'
import { fixtureTasks } from '../fixtures'
import { groupByDoDate } from '../model/tasks'
import { TaskList, type TaskListProps } from './TaskList'

type PreviewState = TaskListProps['status'] | 'empty'

const STATES: readonly PreviewState[] = ['loading', 'error', 'empty', 'ready']

/** Dev-only `#dev-tasks`: TaskList against fixtures, with a state switcher. FE-052 removes it. */
export const TaskListPreview = () => {
  const today = toDateKey(new Date())
  const [state, setState] = useState<PreviewState>('ready')
  const [tasks, setTasks] = useState(() => fixtureTasks(today))
  const [busyIds, setBusyIds] = useState<ReadonlySet<string>>(new Set())

  const remove = (id: string) => setTasks((ts) => ts.filter((t) => t.id !== id))
  const slowRemove = (id: string) => {
    setBusyIds((ids) => new Set([...ids, id]))
    window.setTimeout(() => {
      remove(id)
      setBusyIds((ids) => new Set([...ids].filter((x) => x !== id)))
    }, 800)
  }

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-5 px-4 py-6 md:px-8 md:py-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="label-caps text-3xl md:text-4xl">Task list preview</h1>
        <div role="group" aria-label="Preview state" className="flex gap-1 rounded-lg border p-1">
          {STATES.map((s) => (
            <button
              key={s}
              type="button"
              aria-pressed={state === s}
              onClick={() => {
                setState(s)
                if (s === 'ready') setTasks(fixtureTasks(today))
              }}
              className={cn(
                'label-caps rounded-md px-2.5 py-1 text-xs outline-none transition-colors focus-visible:ring-3 focus-visible:ring-ring/50',
                state === s ? 'bg-muted text-foreground' : 'text-muted-foreground hover:text-foreground',
              )}
            >
              {s}
            </button>
          ))}
        </div>
      </header>
      <p className="text-sm text-muted-foreground">Done removes at once; Let go shows the busy state first.</p>
      <TaskList
        status={state === 'empty' ? 'ready' : state}
        groups={state === 'empty' ? [] : groupByDoDate(tasks, today)}
        today={today}
        busyIds={busyIds}
        onComplete={remove}
        onDrop={slowRemove}
        onRetry={() => setState('ready')}
      />
    </div>
  )
}
