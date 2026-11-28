# BE-100: POST /inbox/accept-all

- **Status:** todo
- **Priority:** 3 (5 = very important … 1 = can hold; see [../README.md](../README.md#priority))
- **Workspace:** backend
- **Epic:** [EPIC-003: Brain-dump inbox + "What now?"](../../Epics/EPIC-003-brain-dump-inbox-what-now.md) §4 story 5, §5.3, §8 · Milestone M7 ([outline](../../outlines/Phase_1_outline_EPIC-003.md))
- **Assigned agent / harness / model:**
- **Depends on:** BE-098
- **Can run in parallel with:** BE-099
- **Public endpoint?** no
- **Review size:** ~80 lines, 3 files, ~8 min

## Goal

`POST /inbox/accept-all?minConfidence=0.8` accepts every visible task or reminder item at or above the threshold, in one go.

## Why this ticket exists

"Inbox triage of 10 items takes under 1 minute" (epic §10) relies on Accept all. The selection rule is a named predicate so the frontend can mirror it for the button's count.

## Read first

- `api/app/inbox/accept.py` (BE-097), the accept route (BE-098).

## Design

- **Pattern:** Specification: `is_auto_acceptable(type, confidence, threshold)` names the rule.

## Packages

None new.

## Details

**Files:** `api/app/inbox/accept.py` (changed: predicate), `api/app/inbox/router.py` (changed), `api/tests/test_inbox_accept_all_api.py` (new).

```python
def is_auto_acceptable(item_type: InboxItemType, confidence: float, threshold: float) -> bool
    # type in {task, reminder} and confidence >= threshold
```

| Request | Response |
|---|---|
| `POST /inbox/accept-all` (default `minConfidence=0.8`) | `200 {"accepted":[{"itemId":"…","taskId":"…"}],"skipped":2}` |
| `minConfidence` outside 0–1 | `422` |
| nothing qualifies | `200 {"accepted":[],"skipped":N}` |
| no / wrong credentials | `401` |

All accepted in one transaction. Fallback items (confidence 0) are never auto-accepted.

## Steps

1. Predicate + tests.
2. Route + tests.

## Tests

- `test_accept_all_takes_only_confident_tasks_and_reminders`
- `test_accept_all_skips_fallback_items`
- `test_accept_all_bad_threshold_422`
- `test_accept_all_requires_credentials`

## Acceptance criteria

- [ ] Uses `task_from_item` for every item (no second conversion path)
- [ ] Endpoint rejects requests without valid credentials
- [ ] Tests pass (`make api-test`)
- [ ] The diff stays within the review size above, or the ticket was split

## How to verify by hand

In `/docs`: with three items (insert via a test dump with the fake parser, or after M8 a real one) call accept-all with 0.8 → only the confident ones become tasks.

## Review guide

1. Predicate used for the selection, nothing inline.

## Out of scope

- Undo for Accept all → not planned.

## Notes / log
