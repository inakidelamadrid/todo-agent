import { isApiError, type createRequest } from '@/lib/api'
import type { ProbeResult } from './gate'
import { createPlaygroundRequest } from './request'
import type {
  TemplateData,
  TemplateInfo,
  TemplatePreview,
  TestMessageResult,
  UpdateLogItem,
} from './types'

export { ApiError, isApiError } from '@/lib/api'

type Request = ReturnType<typeof createRequest>

export interface UpdateFilters {
  readonly limit?: number
  readonly status?: string
  readonly route?: string
}

const BASE = '/admin/telegram'

/** Pure: only the filters that are set become query parameters. They hold no personal data. */
export const updatesQuery = (filters: UpdateFilters = {}): string => {
  const params = new URLSearchParams(
    Object.entries(filters)
      .filter(([, v]) => v !== undefined && v !== '')
      .map(([k, v]) => [k, String(v)]),
  )
  const query = params.toString()
  return query ? `?${query}` : ''
}

/** Typed client over the playground's own request (see `request.ts`). */
export const createPlaygroundApi = (request: Request) => ({
  /** Never throws: a refusal or a network error comes back as `{ ok: false, status }`. */
  probe: async (): Promise<ProbeResult> => {
    try {
      await request<{ readonly enabled: boolean }>('GET', `${BASE}/playground`)
      return { ok: true }
    } catch (e) {
      return { ok: false, status: isApiError(e) ? e.status : 0 }
    }
  },
  listUpdates: async (filters?: UpdateFilters): Promise<readonly UpdateLogItem[]> =>
    (await request<{ readonly items: readonly UpdateLogItem[] }>('GET', `${BASE}/updates${updatesQuery(filters)}`)).items,
  listTemplates: async (): Promise<readonly TemplateInfo[]> =>
    (await request<{ readonly templates: readonly TemplateInfo[] }>('GET', `${BASE}/templates`)).templates,
  previewTemplate: (template: string, data: TemplateData): Promise<TemplatePreview> =>
    request<TemplatePreview>('POST', `${BASE}/templates/preview`, { template, data }),

  /** Always to the owner's own chat: there is no recipient parameter. */
  sendTestMessage: (template: string, data: TemplateData): Promise<TestMessageResult> =>
    request<TestMessageResult>('POST', `${BASE}/test-message`, { template, data }),
})

export type PlaygroundApi = ReturnType<typeof createPlaygroundApi>

export const playgroundApi: PlaygroundApi = createPlaygroundApi(createPlaygroundRequest())
