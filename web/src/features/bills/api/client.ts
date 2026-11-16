import { createRequest, type Fetch } from '@/lib/api'
import { getSessionToken } from '@/lib/sessionToken'
import type { Bill, MonthKey, Payment } from '../model/types'

export { ApiError, isApiError, toFieldErrors, type FieldErrors } from '@/lib/api'

/** Fields the server accepts when creating or replacing a bill (the server owns `id`). */
export type BillInput = Omit<Bill, 'id'>

/** Shape the API returns: a Bill plus server timestamps. */
interface BillDto extends Bill {
  readonly createdAt?: string
  readonly updatedAt?: string
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

/** Build the client around an injectable fetch (tests pass a mock). */
export const createBillsApi = (fetchImpl: Fetch = (...args) => fetch(...args), base = '/api') => {
  const request = createRequest(fetchImpl, base, getSessionToken)

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
