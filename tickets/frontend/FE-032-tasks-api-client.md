# FE-032: Tasks API client

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** frontend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §8 · Milestone M3 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** FE-031, BE-088
- **Can run in parallel with:** FE-051
- **Review size:** ~90 lines, 2 files, ~8 min

## Goal

`createTasksApi()` exposes typed functions for every `/tasks` endpoint.

## Why this ticket exists

The store (FE-052) and later the inbox and What now? need tasks from the API. One typed client keeps URLs and DTO mapping in one file.

## Read first

- `web/src/features/bills/api/client.ts` and `client.test.ts`: `createRequest`, DTO → domain mapping, injectable fetch.

## Design

- **Pattern:** Facade over the shared `request()` helper.

## Packages

None new.

## Details

**Files:** `web/src/features/tasks/api/client.ts` (new), `web/src/features/tasks/api/client.test.ts` (new).

```ts
export type TaskInput = Pick<Task, 'title'> & Partial<Pick<Task, 'notes'|'size'|'energy'|'context'|'doDate'|'dueDate'|'firstStep'|'parentId'>>
export const createTasksApi = (fetchImpl?: Fetch, base = '/api') => ({
  listTasks: (statuses?: readonly TaskStatus[]) => Promise<readonly Task[]>,   // GET /tasks?status=…&status=…
  getTask: (id) => Promise<Task>,
  createTask: (input: TaskInput) => Promise<Task>,
  updateTask: (id, patch: Partial<TaskInput>) => Promise<Task>,
  deleteTask: (id) => Promise<void>,
  completeTask: (id) => Promise<Task>, dropTask: (id) => Promise<Task>, reopenTask: (id) => Promise<Task>,
  snoozeTask: (id, until: DateKey) => Promise<Task>,
})
export const tasksApi = createTasksApi()
```

`toTask(dto)` strips server-only fields (`createdAt`, `updatedAt`, `completedAt`, `droppedAt`, `createdFrom`).

## Steps

1. Client and mapper.
2. Tests with a mock fetch.

## Tests

- `listTasks builds a repeated status query`
- `completeTask posts to /tasks/{id}/complete`
- `snoozeTask sends {until}`
- `409 becomes an ApiError with status 409`
- `sends the bearer token` (via `createRequest`)

## Acceptance criteria

- [ ] One function per endpoint in BE-085–088
- [ ] Tests pass (`npm --prefix web test`) and the build passes (`npm --prefix web run build`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

With `make api-dev` and `make web-dev` running and signed in, in the browser console:

```js
const { tasksApi } = await import('/src/features/tasks/api/client.ts'); await tasksApi.listTasks()
```

Returns the tasks you created in M2.

## Review guide

1. URLs and methods against BE-085–088.
2. `toTask`: the domain type stays clean.

Things that should *not* be in the diff: store, components.

## Out of scope

- Store and screen → FE-052.

## Notes / log
