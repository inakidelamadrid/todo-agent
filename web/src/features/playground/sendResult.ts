import type { TestMessageResult } from './types'

export type SendOutcome =
  | { readonly ok: true; readonly result: TestMessageResult }
  | { readonly ok: false; readonly status: number; readonly detail: string }

export interface SendMessage {
  readonly tone: 'good' | 'bad'
  readonly text: string
}

/** Pure: what the Test message tab says after a send, from the result or the refusal. */
export const describeSendResult = (input: SendOutcome): SendMessage => {
  if (input.ok) return { tone: 'good', text: 'Sent. Check your Telegram chat.' }
  if (input.status === 429) return { tone: 'bad', text: 'Limit reached: 10 test messages per hour.' }
  if (input.status === 409) return { tone: 'bad', text: 'Telegram is not configured.' }
  if (input.status === 502) return { tone: 'bad', text: 'Telegram refused the message. Try again in a minute.' }
  return { tone: 'bad', text: input.detail.trim() || 'Couldn’t send the test message. Try again.' }
}
