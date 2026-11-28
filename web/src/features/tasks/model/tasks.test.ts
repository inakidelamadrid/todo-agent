import { describe, expect, it } from 'vitest'
import { dateLabel, groupByDoDate, SIZE_LABEL } from './tasks'
import type { Task } from './types'

const TODAY = '2026-11-27' // a Friday

const task = (title: string, extra: Partial<Task> = {}): Task => ({
  id: title,
  title,
  notes: '',
  size: 'S',
  energy: 'medium',
  context: 'anywhere',
  doDate: null,
  dueDate: null,
  firstStep: '',
  parentId: null,
  status: 'active',
  snoozedUntil: null,
  ...extra,
})

describe('dateLabel', () => {
  it.each([
    [{ dueDate: '2026-11-27' }, 'Due today'],
    [{ dueDate: '2026-11-28' }, 'Due tomorrow'],
    [{ dueDate: '2026-12-01' }, 'Due Tue'],
    [{ dueDate: '2026-12-03' }, 'Due Thu'],
    [{ dueDate: '2026-12-04' }, 'Due 4 Dec'],
    [{ doDate: '2026-11-27' }, 'Planned for today'],
    [{ doDate: '2026-11-28' }, 'Planned for tomorrow'],
    [{ doDate: '2026-11-30' }, 'Planned for Mon'],
    [{ doDate: '2027-01-15' }, 'Planned for 15 Jan'],
  ])('%j reads "%s"', (dates, text) => {
    expect(dateLabel(task('x', dates), TODAY)).toEqual({ text, tone: 'normal' })
  })

  it('dateLabel says "Past its date" in a muted tone', () => {
    expect(dateLabel(task('x', { dueDate: '2026-11-20' }), TODAY)).toEqual({ text: 'Past its date', tone: 'muted' })
    expect(dateLabel(task('x', { doDate: '2026-11-26' }), TODAY)).toEqual({ text: 'Past its date', tone: 'muted' })
  })

  it('dateLabel prefers due date over do date', () => {
    expect(dateLabel(task('x', { doDate: '2026-11-27', dueDate: '2026-11-28' }), TODAY)?.text).toBe('Due tomorrow')
  })

  it('returns null without dates', () => {
    expect(dateLabel(task('x'), TODAY)).toBeNull()
  })

  it('never sounds alarmed', () => {
    const dates = ['2026-01-01', '2026-11-26', TODAY, '2026-11-28', '2026-12-02', '2027-03-01']
    for (const d of dates) {
      for (const label of [dateLabel(task('x', { dueDate: d }), TODAY), dateLabel(task('x', { doDate: d }), TODAY)]) {
        expect(label?.text).not.toMatch(/overdue|late|!/i)
      }
    }
  })
})

describe('groupByDoDate', () => {
  it('groupByDoDate puts past-due tasks in today', () => {
    const groups = groupByDoDate([task('late', { dueDate: '2026-11-01', doDate: '2026-12-10' })], TODAY)
    expect(groups.map((g) => g.key)).toEqual(['today'])
  })

  it('groupByDoDate omits empty groups', () => {
    expect(groupByDoDate([task('a'), task('b')], TODAY).map((g) => g.key)).toEqual(['anytime'])
    expect(groupByDoDate([], TODAY)).toEqual([])
  })

  it('splits today, upcoming and anytime in that order', () => {
    const groups = groupByDoDate(
      [task('free'), task('later', { doDate: '2026-12-02' }), task('now', { doDate: TODAY })],
      TODAY,
    )
    expect(groups.map((g) => [g.key, g.label, g.tasks.map((t) => t.title)])).toEqual([
      ['today', 'Today', ['now']],
      ['upcoming', 'Upcoming', ['later']],
      ['anytime', 'Anytime', ['free']],
    ])
  })

  it('sorts by due date, then title, without mutating the input', () => {
    const input = [task('b', { doDate: TODAY }), task('a', { doDate: TODAY }), task('c', { doDate: TODAY, dueDate: '2026-11-30' })]
    const [today] = groupByDoDate(input, TODAY)
    expect(today.tasks.map((t) => t.title)).toEqual(['c', 'a', 'b'])
    expect(input.map((t) => t.title)).toEqual(['b', 'a', 'c'])
  })
})

describe('SIZE_LABEL', () => {
  it('SIZE_LABEL covers every size', () => {
    expect(Object.keys(SIZE_LABEL).sort()).toEqual(['L', 'M', 'S', 'XL', 'XS'])
    expect(SIZE_LABEL.M).toBe('M · 45 min')
  })
})
