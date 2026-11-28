import { describe, expect, it } from 'vitest'
import { fixtureTasks } from '../fixtures'
import { CONTEXT_LABEL, taskRow } from './taskRow'
import type { TaskContext } from './types'

const TODAY = '2026-11-27'
const [base] = fixtureTasks(TODAY)

describe('taskRow', () => {
  it('taskRow uses the muted tone for past its date', () => {
    expect(taskRow({ ...base, doDate: null, dueDate: '2026-11-20' }, TODAY).date).toEqual({ text: 'Past its date', tone: 'muted' })
  })

  it('taskRow hides an empty first step', () => {
    expect(taskRow({ ...base, firstStep: '' }, TODAY).firstStep).toBeNull()
    expect(taskRow({ ...base, firstStep: '   ' }, TODAY).firstStep).toBeNull()
    expect(taskRow({ ...base, firstStep: 'Open the app' }, TODAY).firstStep).toBe('Open the app')
  })

  it('taskRow labels every context', () => {
    const contexts: readonly TaskContext[] = ['home', 'computer', 'phone', 'errand', 'anywhere']
    for (const context of contexts) {
      expect(taskRow({ ...base, context }, TODAY).contextLabel).toBe(CONTEXT_LABEL[context])
    }
    expect(new Set(Object.values(CONTEXT_LABEL)).size).toBe(contexts.length)
  })

  it('shows the size label', () => {
    expect(taskRow({ ...base, size: 'XL' }, TODAY).sizeLabel).toBe('XL · break it down')
  })
})
