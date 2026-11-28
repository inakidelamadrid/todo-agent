# BE-102: What now? scoring and ranking

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §5.5 · Milestone M9 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-101
- **Can run in parallel with:** BE-104
- **Public endpoint?** no
- **Review size:** ~140 lines, 2 files, ~14 min

## Goal

`score` gives each candidate a total and its named factors (urgency, fit, age, momentum, skip penalty); `rank` orders them deterministically and `pick` returns one plus up to two alternates.

## Why this ticket exists

The epic wants a transparent, rule-based choice (§5.5, risk "suggestion distrust"). Keeping every factor as a named number lets the *why* (BE-103) explain it and lets you print it.

## Read first

- `api/app/now/domain.py` (BE-101).

## Design

- **Pattern:** Pipeline of pure functions: `score` per task → `rank` → `pick`. Weights are module constants, not magic numbers.

## Packages

None new.

## Details

**Files:** `api/app/now/scoring.py` (new), `api/tests/test_now_scoring.py` (new).

```python
@dataclass(frozen=True)
class Factors: urgency: float; fit: float; age: float; momentum: float; skip_penalty: float   # each 0..1

@dataclass(frozen=True)
class Scored: task: TaskSnapshot; factors: Factors; total: float

WEIGHTS = MappingProxyType({"urgency": 3.0, "fit": 2.0, "age": 1.0, "momentum": 1.5, "skip_penalty": -2.0})

def score(task, req, today, *, recent_skips: frozenset[UUID], started_parents: frozenset[UUID]) -> Scored
def rank(scored: Iterable[Scored]) -> tuple[Scored, ...]
def pick(ranked: Sequence[Scored]) -> tuple[Scored, tuple[Scored, ...]] | None   # (choice, ≤2 alternates)
```

| Factor | Rule |
|---|---|
| urgency | due date: past → 1.0; today → 0.9; tomorrow → 0.8; in 2–7 days → 0.7 down to 0.3 linearly; later or none → 0 |
| fit | half energy (task energy ≤ requested → 1, one level above → 0.4, two → 0; no request → 0.7) + half size (`minutes_of(size) / available`, closer to 1 is better; no time → 0.7) |
| age | days since `created_at` / 14, capped at 1 |
| momentum | 1 when `parent_id` is in `started_parents` (a sibling step is done) |
| skip_penalty | 1 when the task is in `recent_skips` |

`total = Σ weight × factor`. Ties: earlier due date, then older `created_at`, then `id`, so the same inputs always give the same order.

## Steps

1. Factors one by one, each with tests.
2. `score`, `rank`, `pick`.

## Tests

- `test_due_tomorrow_beats_no_due_date`
- `test_low_energy_request_prefers_low_energy_task`
- `test_recent_skip_drops_rank`
- `test_momentum_lifts_sibling_steps`
- `test_rank_is_deterministic_on_ties`
- `test_pick_returns_at_most_two_alternates`
- `test_pick_empty_returns_none`

## Acceptance criteria

- [ ] Pure; no randomness, no clock
- [ ] Every factor stays within 0..1
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

```bash
cd api && uv run python -m app.now.scoring --demo
```

A `__main__` block prints a small table for three sample tasks (due tomorrow S low, no date M high, past date XS low) with each factor and the total; the due-tomorrow one should not lose to the no-date one.

## Review guide

1. Weights in one constant.
2. Factor table vs code.
3. Tie-break order.

## Out of scope

- Learning time-of-day preferences → deferred.

## Notes / log
