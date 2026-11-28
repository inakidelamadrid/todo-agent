import { useEffect } from 'react'
import { toast } from 'sonner'
import { toDateKey } from '@/features/bills/model/schedule'
import { TaskList } from './components/TaskList'
import { groupByDoDate } from './model/tasks'
import { type LoadError, useTasksStore } from './store/useTasksStore'

const errorMessage = (error: LoadError | null): string | undefined =>
  error && (error.status === 0 || error.status >= 500)
    ? 'The tasks API isn’t answering. Check that it’s running (make api-dev), then try again.'
    : error?.message

const couldNotSave = () => toast.error('Couldn’t save that. It’s back on your list.')

const summary = (count: number, todayCount: number): string =>
  count === 0 ? 'A clear list.' : `${count} ${count === 1 ? 'task' : 'tasks'} · ${todayCount} for today`

export const TasksScreen = () => {
  const tasks = useTasksStore((s) => s.tasks)
  const status = useTasksStore((s) => s.status)
  const error = useTasksStore((s) => s.error)
  const busyIds = useTasksStore((s) => s.busyIds)
  const { load, complete, drop, reopen } = useTasksStore.getState()

  useEffect(() => {
    if (useTasksStore.getState().status === 'idle') void load()
  }, [load])

  const today = toDateKey(new Date())
  const groups = groupByDoDate(tasks, today)
  const todayCount = groups.find((g) => g.key === 'today')?.tasks.length ?? 0

  const onComplete = (id: string) => {
    complete(id).then(() => toast('Done.'), couldNotSave)
  }

  const onDrop = (id: string) => {
    drop(id).then(
      () =>
        toast('Let go. It’s off your list.', {
          action: { label: 'Undo', onClick: () => void reopen(id).catch(() => toast.error('Couldn’t bring it back. Try again.')) },
        }),
      couldNotSave,
    )
  }

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-5 px-4 py-6 md:px-8 md:py-8 [&>*]:min-w-0">
      <header>
        <h1 className="font-heading text-4xl font-semibold tracking-tight md:text-5xl">Tasks</h1>
        <p className="mt-1 text-muted-foreground" aria-live="polite">
          {status === 'ready' ? summary(tasks.length, todayCount) : status === 'error' ? 'Tasks unavailable' : 'Loading tasks…'}
        </p>
      </header>
      <TaskList
        status={status === 'ready' ? 'ready' : status === 'error' ? 'error' : 'loading'}
        errorMessage={errorMessage(error)}
        groups={groups}
        today={today}
        busyIds={busyIds}
        onComplete={onComplete}
        onDrop={onDrop}
        onRetry={() => void load()}
      />
    </div>
  )
}
