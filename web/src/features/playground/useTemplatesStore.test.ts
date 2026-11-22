import { describe, expect, it, vi } from 'vitest'
import { ApiError } from '@/lib/api'
import { createTemplatesStore } from './useTemplatesStore'

const templates = [{ name: 'help', fields: [] }, { name: 'unknown_command', fields: ['command'] }]
const preview = { html: 'I don’t know <code>/x</code>. Try /help.', length: 37 }

const setup = (previewTemplate = vi.fn().mockResolvedValue(preview)) => {
  const listTemplates = vi.fn().mockResolvedValue(templates)
  return { store: createTemplatesStore({ listTemplates, previewTemplate }), listTemplates, previewTemplate }
}

describe('useTemplatesStore', () => {
  it('loads the templates once', async () => {
    const { store, listTemplates } = setup()
    await store.getState().load()
    await store.getState().load()
    expect(store.getState()).toMatchObject({ templates, status: 'ready' })
    expect(listTemplates).toHaveBeenCalledTimes(1)
  })

  it('resets data and preview when another template is selected', async () => {
    const { store } = setup()
    await store.getState().load()
    store.getState().select('unknown_command')
    store.getState().setField('command', 'x')
    await store.getState().runPreview()
    store.getState().select('help')
    expect(store.getState()).toMatchObject({ selected: 'help', data: {}, preview: null, previewStatus: 'idle' })
  })

  it('sets the preview from the API', async () => {
    const { store, previewTemplate } = setup()
    await store.getState().load()
    store.getState().select('unknown_command')
    store.getState().setField('command', 'x')
    await store.getState().runPreview()
    expect(previewTemplate).toHaveBeenCalledWith('unknown_command', { command: 'x' })
    expect(store.getState()).toMatchObject({ preview, previewStatus: 'ready' })
  })

  it('maps a missing-field 422 to that field, and clears it on edit', async () => {
    const { store } = setup(vi.fn().mockRejectedValue(new ApiError(422, 'Missing field: command')))
    await store.getState().load()
    store.getState().select('unknown_command')
    await store.getState().runPreview()
    expect(store.getState()).toMatchObject({ previewStatus: 'error', fieldErrors: { command: 'Missing field: command' } })
    store.getState().setField('command', 'x')
    expect(store.getState().fieldErrors).toEqual({})
  })
})
