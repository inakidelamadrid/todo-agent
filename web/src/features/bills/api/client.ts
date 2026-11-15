import type { Bill, MonthKey, Payment } from '../model/types'

/** Fields the server accepts when creating or replacing a bill (the server owns `id`). */
export type BillInput = Omit<Bill, 'id'>

/** Shape the API returns: a Bill plus server timestamps. */
interface BillDto extends Bill {
  readonly createdAt?: string
  readonly updatedAt?: string
}

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

/** Pure: strip server-only fields so the store keeps the shared domain shape. */
export const toBill = ({ id, name, note, line, currency, estimatedCents, dueDay, recurrence, startMonth }: BillDto): Bill => ({
  id,
  name,
  note,
  line,
  currency,
  estimatedCents,
  dueDay,
  recurrence,
  startMonth,
})

export const toBillInput = ({ id: _id, ...input }: Bill): BillInput => input

type Fetch = typeof fetch

/** Build the client around an injectable fetch (tests pass a mock). */
export const createBillsApi = (fetchImpl: Fetch = (...args) => fetch(...args), base = '/api') => {
  const request = async <T>(method: string, path: string, body?: unknown): Promise<T> => {
    const response = await fetchImpl(`${base}${path}`, {
      method,
      headers: body === undefined ? { Accept: 'application/json' } : { Accept: 'application/json', 'Content-Type': 'application/json' },
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

  return {
    listBills: async (): Promise<readonly Bill[]> => (await request<readonly BillDto[]>('GET', '/bills')).map(toBill),
    createBill: async (input: BillInput): Promise<Bill> => toBill(await request<BillDto>('POST', '/bills', input)),
    updateBill: async (id: string, patch: Partial<BillInput>): Promise<Bill> =>
      toBill(await request<BillDto>('PATCH', `/bills/${id}`, patch)),
    deleteBill: (id: string): Promise<void> => request<void>('DELETE', `/bills/${id}`),
    listPayments: (month: MonthKey): Promise<readonly Payment[]> =>
      request<readonly Payment[]>('GET', `/payments?month=${encodeURIComponent(month)}`),
    putPayment: (payment: Payment): Promise<Payment> =>
      request<Payment>('PUT', `/bills/${payment.billId}/payments/${payment.period}`, {
        actualCents: payment.actualCents,
        paidAt: payment.paidAt,
      }),
    deletePayment: (billId: string, period: MonthKey): Promise<void> =>
      request<void>('DELETE', `/bills/${billId}/payments/${period}`),
  }
}

export type BillsApi = ReturnType<typeof createBillsApi>

export const billsApi: BillsApi = createBillsApi()
