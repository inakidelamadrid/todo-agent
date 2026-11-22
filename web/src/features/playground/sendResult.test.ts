import { describe, expect, it } from 'vitest'
import { describeSendResult } from './sendResult'

const refused = (status: number, detail = '') => ({ ok: false as const, status, detail })

describe('describeSendResult', () => {
  it('is good when sent', () => {
    expect(describeSendResult({ ok: true, result: { messageId: 123 } })).toEqual({ tone: 'good', text: 'Sent. Check your Telegram chat.' })
  })

  it('names the limit on 429', () => {
    expect(describeSendResult(refused(429, 'Test message limit reached (10 per hour)'))).toEqual({
      tone: 'bad',
      text: 'Limit reached: 10 test messages per hour.',
    })
  })

  it('says Telegram is not configured on 409', () => {
    expect(describeSendResult(refused(409, 'TELEGRAM_BOT_TOKEN is not set'))).toEqual({ tone: 'bad', text: 'Telegram is not configured.' })
  })

  it('says Telegram refused on 502', () => {
    expect(describeSendResult(refused(502, 'Telegram refused the message (SendFailed)'))).toEqual({
      tone: 'bad',
      text: 'Telegram refused the message. Try again in a minute.',
    })
  })

  it('falls back to the detail, then to a generic line', () => {
    expect(describeSendResult(refused(404, 'Unknown template'))).toEqual({ tone: 'bad', text: 'Unknown template' })
    expect(describeSendResult(refused(0))).toEqual({ tone: 'bad', text: 'Couldn’t send the test message. Try again.' })
  })
})
