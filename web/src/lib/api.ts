export type FieldErrors = Readonly<Record<string, string>>

/** Typed failure for every non-2xx response or network error (status 0). */
export class ApiError extends Error {
  readonly status: number
  readonly fieldErrors: FieldErrors

  constructor(status: number, message: string, fieldErrors: FieldErrors = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.fieldErrors = fieldErrors
  }
}

export const isApiError = (e: unknown): e is ApiError => e instanceof ApiError

interface ValidationItem {
  readonly loc?: readonly (string | number)[]
  readonly msg?: string
}

/** Map FastAPI 422 `detail` items to `{ camelCaseField: message }`. */
export const toFieldErrors = (detail: unknown): FieldErrors =>
  Array.isArray(detail)
    ? Object.fromEntries(
        (detail as readonly ValidationItem[])
          .filter((d) => d.loc && d.loc.length > 1)
          .map((d) => [String(d.loc![d.loc!.length - 1]), d.msg ?? 'Invalid value']),
      )
    : {}

const messageFor = (status: number, detail: unknown): string => {
  if (typeof detail === 'string') return detail
  if (status === 401) return 'The API rejected the key'
  if (status === 404) return 'Not found'
  if (status === 422) return 'Some fields are invalid'
  return `Request failed (${status})`
}

export type Fetch = typeof fetch

export type GetToken = () => Promise<string | null>

/**
 * Build `request` around an injectable fetch (tests pass a mock) and an optional token getter.
 * The token is read per call and never stored; a missing, null or failing getter sends no header.
 */
export const createRequest = (fetchImpl: Fetch, base: string, getToken?: GetToken) => {
  const request = async <T>(method: string, path: string, body?: unknown): Promise<T> => {
    const token = getToken ? await getToken().catch(() => null) : null
    const response = await fetchImpl(`${base}${path}`, {
      method,
      headers: {
        Accept: 'application/json',
        ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    }).catch(() => {
      throw new ApiError(0, 'Can’t reach the bills API')
    })
    if (response.status === 204) return undefined as T
    const payload: unknown = await response.json().catch(() => null)
    if (!response.ok) {
      const detail = (payload as { detail?: unknown } | null)?.detail
      throw new ApiError(response.status, messageFor(response.status, detail), response.status === 422 ? toFieldErrors(detail) : {})
    }
    return payload as T
  }

  return request
}
