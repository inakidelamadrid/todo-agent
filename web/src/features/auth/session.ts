import type { createRequest } from '@/lib/api'

export type Request = ReturnType<typeof createRequest>

export interface Me {
  readonly userId: string
  readonly kind: 'user'
  readonly roles: readonly string[]
}

interface MeDto {
  readonly userId: string
  readonly kind: 'user'
  readonly roles?: readonly string[]
}

/** Pure: the only place that reads `roles`. No session, or a failed load, is never an admin. */
export const isAdmin = (me: Me | null): boolean => me?.roles.includes('admin') ?? false

/** Pure: a missing `roles` field is treated as no roles. */
export const toMe = ({ userId, kind, roles }: MeDto): Me => ({ userId, kind, roles: roles ?? [] })

export const fetchMe = async (request: Request): Promise<Me> => toMe(await request<MeDto>('GET', '/me'))
