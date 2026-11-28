# Manual validation: EPIC-003 M4 — Brain dump through the API

Branch: `idelamadrid/EPIC-003-M4-brain-dump-api`
Tickets: BE-089, BE-090, BE-092

## How to validate

Run these commands, then check the boxes yourself. An agent must never
check a box for you.

```bash
# 1. Start the database if it isn't running
make db-up

# 2. Apply migrations
make api-migrate

# 3. Run the API test suite
make api-test

# 4. Start the API
make api-dev
```

Use the running API at `http://127.0.0.1:8000/docs` or `curl` with an API
key from `api/.env` (`API_KEYS`).

---

## BE-089: Inbox schemas

### Schema shape

- [ ] `DumpIn` accepts `rawText` (1–4000 chars) and optional `source`.
- [ ] `POST /inbox/dumps` with empty/whitespace `rawText` returns `422`.
- [ ] A candidate union rejects the wrong fields for its `type` (e.g. a
  `task` with `amountCents` or an `expense` without `amountCents`
  returns `422`).
- [ ] `ParseDumpResult` rejects an empty `items` array.

### Discriminated union

- [ ] `task`, `reminder`, `note`, and `expense` candidates all validate
  when their required fields are present.
- [ ] `InboxItemOut` includes `size`, `energy`, `context`, and
  `firstStep` for task items.
- [ ] `POST /inbox/dumps` payload looks right in `/docs` and uses
  camelCase on the wire.

---

## BE-090: DumpParser port

### Fake parser (tests)

- [ ] `tests/test_inbox/test_parser.py` passes.
- [ ] `fake_parser(...)` returns the canned items regardless of input.

### drafts_from_result

- [ ] `tests/test_inbox/test_domain.py` passes.
- [ ] For a `task` candidate, the draft contains `size`, `energy`,
  `context`, `doDate`, `dueDate`, and `firstStep`.
- [ ] For a `reminder` candidate, the draft contains `doDate`.
- [ ] For a `note` candidate, the draft contains `body`.
- [ ] For an `expense` candidate, the draft contains `amountCents` and
  `currency`.
- [ ] Every key in every draft is an `InboxItem` column.

### Unconfigured parser (fallback behaviour)

- [ ] With no parser configured, `POST /inbox/dumps` stores the dump and
  creates exactly one low-confidence fallback `task` item holding the
  original `rawText`.
- [ ] The fallback item appears in `GET /inbox` with
  `confidence: "low"` and `type: "task"`.

> Note: the wiring routes (BE-095/BE-096) are not in this branch, so test
> the fallback behaviour with a direct Python snippet against the
> repository if needed, or wait for the next slice.

---

## BE-092: `dumps` and `inbox_items` tables

### Migration

- [ ] `make api-migrate` runs without errors and reports all three:
  - `Running upgrade 483ebd9b1c91 -> 810dec36a5fd, create dumps and inbox_items`
  - `Running upgrade 810dec36a5fd -> fc5e5b905e0d, fix inbox_items snoozed_until type to date`
  - `Running upgrade fc5e5b905e0d -> 40bb439f8e73, add inbox_items task triage columns`
- [ ] All three migrations are listed by `cd api && uv run alembic history`.

### Table structure

Run:

```bash
make db-psql
\d dumps
\d inbox_items
```

- [ ] `dumps` has columns: `id`, `raw_text`, `source`, `created_at`.
- [ ] `inbox_items` has columns: `id`, `dump_id`, `type`, `status`,
  `summary`, `confidence`, `size`, `energy`, `context`, `first_step`,
  `body`, `amount_cents`, `currency`, `do_date`, `due_date`,
  `snoozed_until`, `created_at`.
- [ ] `inbox_items.dump_id` has a foreign key to `dumps(id)` with
  `ON DELETE CASCADE`.
- [ ] `inbox_items.snoozed_until` has type `date` (not `timestamp`).
- [ ] Check constraints exist for `dumps.source`, `inbox_items.type`,
  `inbox_items.status`, `inbox_items.confidence`, `inbox_items.size`,
  `inbox_items.energy`, `inbox_items.context`, and `summary`/`first_step`
  length.

### Task triage columns

In `make db-psql`:

```sql
INSERT INTO dumps (id, raw_text, source)
VALUES ('33333333-3333-3333-3333-333333333333'::uuid, 'gym 600', 'web');

INSERT INTO inbox_items (
  id, dump_id, type, status, summary, confidence,
  size, energy, context, first_step
)
VALUES (
  '44444444-4444-4444-4444-444444444444'::uuid,
  '33333333-3333-3333-3333-333333333333'::uuid,
  'task', 'new', 'Go to gym', 'high',
  'S', 'low', 'errand', 'Pack bag'
);

SELECT size, energy, context, first_step FROM inbox_items
WHERE id = '44444444-4444-4444-4444-444444444444'::uuid;
```

- [ ] The row returns `size=S`, `energy=low`, `context=errand`,
  `first_step=Pack bag`.
- [ ] Inserting `size='XXL'` violates the check constraint.

### Cascade delete

In `make db-psql`:

```sql
INSERT INTO dumps (id, raw_text, source)
VALUES ('11111111-1111-1111-1111-111111111111'::uuid, 'test', 'web');

INSERT INTO inbox_items (id, dump_id, type, status, summary, confidence)
VALUES ('22222222-2222-2222-2222-222222222222'::uuid,
        '11111111-1111-1111-1111-111111111111'::uuid,
        'task', 'new', 'test', 'low');

DELETE FROM dumps WHERE id = '11111111-1111-1111-1111-111111111111'::uuid;
SELECT * FROM inbox_items WHERE id = '22222222-2222-2222-2222-222222222222'::uuid;
```

- [ ] The delete removes the dump and the dependent inbox item.
- [ ] The final `SELECT` returns zero rows.

---

## Automated checks

- [ ] `make api-test` passes.
- [ ] `cd api && uv run ruff check app/inbox tests/test_inbox` passes.

---

## Sign-off

Date: ___________
Validator: ___________

- [ ] I completed every section above and the branch is ready for the next
  slice (BE-093 / BE-094 / BE-095).
