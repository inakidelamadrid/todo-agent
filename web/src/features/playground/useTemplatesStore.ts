import { create } from 'zustand'
import type { FieldErrors } from '@/lib/api'
import { type PlaygroundApi, playgroundApi } from './api'
import type { LoadStatus } from './components/TemplatePreviewPanel'
import { fieldErrorsFrom, findTemplate } from './templateForm'
import type { TemplateData, TemplateInfo, TemplatePreview } from './types'

export interface TemplatesState {
  readonly templates: readonly TemplateInfo[]
  readonly status: LoadStatus
  readonly error: string | null
  readonly selected: string | null
  readonly data: TemplateData
  readonly fieldErrors: FieldErrors
  readonly preview: TemplatePreview | null
  readonly previewStatus: LoadStatus
  readonly previewError: string | null
}

export interface TemplatesActions {
  /** Loads once; `force` reloads (Try again). */
  readonly load: (options?: { readonly force?: boolean }) => Promise<void>
  /** Picking a template clears the fields and the previous preview. */
  readonly select: (name: string) => void
  readonly setField: (name: string, value: string) => void
  readonly runPreview: () => Promise<void>
}

const errorOf = (e: unknown) => ({
  status: typeof e === 'object' && e !== null && 'status' in e ? Number((e as { status: unknown }).status) : 0,
  message: e instanceof Error ? e.message : 'Something went wrong',
  fieldErrors: typeof e === 'object' && e !== null && 'fieldErrors' in e ? (e as { fieldErrors: FieldErrors }).fieldErrors : {},
})

const cleared = { data: {}, fieldErrors: {}, preview: null, previewStatus: 'idle', previewError: null } as const

/** Store factory with an injectable API; shared by the Templates and Test message tabs. */
export const createTemplatesStore = (api: Pick<PlaygroundApi, 'listTemplates' | 'previewTemplate'>) =>
  create<TemplatesState & TemplatesActions>()((set, get) => ({
    templates: [],
    status: 'idle',
    error: null,
    selected: null,
    ...cleared,

    load: async (options) => {
      const { status } = get()
      if (!options?.force && (status === 'loading' || status === 'ready')) return
      set({ status: 'loading', error: null })
      try {
        set({ templates: await api.listTemplates(), status: 'ready' })
      } catch (e) {
        set({ status: 'error', error: errorOf(e).message })
      }
    },

    select: (name) => set({ selected: name, ...cleared }),

    setField: (name, value) =>
      set((s) => ({
        data: { ...s.data, [name]: value },
        fieldErrors: Object.fromEntries(Object.entries(s.fieldErrors).filter(([k]) => k !== name)),
      })),

    runPreview: async () => {
      const { selected, data, templates } = get()
      if (!selected) return
      set({ previewStatus: 'loading', previewError: null, fieldErrors: {} })
      try {
        set({ preview: await api.previewTemplate(selected, data), previewStatus: 'ready' })
      } catch (e) {
        const error = errorOf(e)
        const fieldErrors = fieldErrorsFrom(error, findTemplate(templates, selected)?.fields ?? [])
        set({ preview: null, previewStatus: 'error', previewError: error.message, fieldErrors })
      }
    },
  }))

export const useTemplatesStore = createTemplatesStore(playgroundApi)
