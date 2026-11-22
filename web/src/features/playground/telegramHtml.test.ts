import { describe, expect, it } from 'vitest'
import { parseTelegramHtml } from './telegramHtml'

describe('parseTelegramHtml', () => {
  it('returns plain text as one text node', () => {
    expect(parseTelegramHtml('Hello there')).toEqual([{ kind: 'text', text: 'Hello there' }])
    expect(parseTelegramHtml('')).toEqual([])
  })

  it('turns bold, italic and code into nodes', () => {
    expect(parseTelegramHtml('<b>Bills</b> due: <i>soon</i>, run <code>/now</code>')).toEqual([
      { kind: 'b', text: 'Bills' },
      { kind: 'text', text: ' due: ' },
      { kind: 'i', text: 'soon' },
      { kind: 'text', text: ', run ' },
      { kind: 'code', text: '/now' },
    ])
  })

  it('decodes entities in text', () => {
    expect(parseTelegramHtml('a &lt; b &amp;&amp; c &gt; d &amp;lt;')).toEqual([{ kind: 'text', text: 'a < b && c > d &lt;' }])
  })

  it('keeps unknown tags as literal text', () => {
    expect(parseTelegramHtml('<script>alert(1)</script> <u>x</u>')).toEqual([{ kind: 'text', text: '<script>alert(1)</script> <u>x</u>' }])
  })

  it('keeps escaped data inside code as text', () => {
    expect(parseTelegramHtml('I don’t know <code>/&lt;b&gt;x&lt;/b&gt;</code>. Try /help.')).toEqual([
      { kind: 'text', text: 'I don’t know ' },
      { kind: 'code', text: '/<b>x</b>' },
      { kind: 'text', text: '. Try /help.' },
    ])
  })

  it('degrades nested tags to text', () => {
    expect(parseTelegramHtml('<b>a <i>b</i></b>')).toEqual([
      { kind: 'text', text: '<b>a ' },
      { kind: 'i', text: 'b' },
      { kind: 'text', text: '</b>' },
    ])
  })
})
