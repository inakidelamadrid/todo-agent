# BE-101: What now? request and candidate rules

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §4 story 9, §5.5 · Milestone M9 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-081
- **Can run in parallel with:** M4–M7 tickets
- **Public endpoint?** no
- **Review size:** ~90 lines, 3 files, ~10 min

## Goal

`api/app/now/` defines the What now? request and a pure `is_candidate` predicate: which tasks may be suggested for this energy, time and context today.

## Why this ticket exists

The engine is split into three pure steps (filter, score, explain) so each can be read and tried alone. Filtering comes first: it is the hard "no" (an L task can't fit 15 minutes).

## Read first

- `api/app/tasks/domain.py` (BE-081): `SIZE_MINUTES`, `is_awake`.
- **Specification:** a named predicate reused wherever the rule applies, combined with `and`.

## Design

- **Pattern:** Specification: small predicates (`fits_time`, `fits_context`, `is_planned_by`) combined into `is_candidate`.

## Packages

None new.

## Details

**Files:** `api/app/now/__init__.py`, `api/app/now/schemas.py` (new: `NowRequest`), `api/app/now/domain.py` (new), `api/tests/test_now_candidates.py` (new).

```python
class NowRequest(_CamelModel):
    energy: Energy | None = None                         # skipped → no energy preference
    available_minutes: Literal[5, 15, 30, 60] | None = None   # 60 means "60+"; skipped → no time filter
    context: TaskContext | None = None

@dataclass(frozen=True)
class TaskSnapshot:   # the fields the engine needs, built from a Task row by the route
    id: UUID; title: str; first_step: str; size: TaskSize; energy: Energy; context: TaskContext
    status: TaskStatus; snoozed_until: date | None; do_date: date | None; due_date: date | None
    parent_id: UUID | None; created_at: datetime; has_open_children: bool

def fits_time(size: TaskSize, minutes: int | None) -> bool      # None → True; XL → False; 60 → up to L
def fits_context(task_ctx: TaskContext, wanted: TaskContext | None) -> bool   # None or 'anywhere' on either side → True
def is_planned_by(do_date: date | None, today: date) -> bool    # no do date, or do date <= today
def is_candidate(task: TaskSnapshot, req: NowRequest, today: date) -> bool
```

`is_candidate` = `is_awake` and `fits_time` and `fits_context` and `is_planned_by` and **not** `has_open_children` (a parent with open steps is represented by its steps). Energy is a score factor, not a filter (BE-102).

## Steps

1. `NowRequest`, `TaskSnapshot`.
2. Predicates + tests.

## Tests

- `test_l_task_does_not_fit_15_minutes`
- `test_l_task_fits_60_plus`
- `test_xl_never_fits`
- `test_skipped_time_means_no_filter`
- `test_anywhere_matches_any_context`
- `test_future_do_date_excluded`
- `test_parent_with_open_children_excluded`
- `test_snoozed_until_tomorrow_excluded`

## Acceptance criteria

- [ ] Pure; no session
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
cd api && uv run python -c "from app.now.domain import fits_time; print(fits_time('L', 15), fits_time('L', 60), fits_time('XS', None))"
```

Prints `False True True`.

## Review guide

1. Each predicate is one line of logic with a name.
2. Energy is not filtered here.

## Out of scope

- Scoring → BE-102.

## Notes / log
