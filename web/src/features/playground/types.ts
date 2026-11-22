/** Wire types for the playground API (camelCase, as the API sends them). */

export type UpdateStatus = 'received' | 'processed' | 'failed'

/** Metadata only: the API never returns message text, chat or message IDs. */
export interface UpdateLogItem {
  readonly updateId: number
  readonly kind: string
  readonly route: string
  readonly status: UpdateStatus
  readonly receivedAt: string
  /** True for updates made by the playground's Run for real (negative update IDs). */
  readonly playground: boolean
}

export interface TemplateInfo {
  readonly name: string
  readonly fields: readonly string[]
}

export interface TemplatePreview {
  readonly html: string
  readonly length: number
}

export type TemplateData = Readonly<Record<string, string>>

/** Sent right away to the owner's own chat; the ID is Telegram's message ID. */
export interface TestMessageResult {
  readonly messageId: number
}
