export type TgNode = { readonly kind: 'text' | 'b' | 'i' | 'code'; readonly text: string }

/** Only these three entities, as Telegram's HTML style needs; `&amp;` last so `&amp;lt;` stays `&lt;`. */
const decode = (s: string): string => s.replaceAll('&lt;', '<').replaceAll('&gt;', '>').replaceAll('&amp;', '&')

/** A supported tag whose content holds no other tag; anything else is left as literal text. */
const TAG = /<(b|i|code)>([^<]*)<\/\1>/g

const pushText = (nodes: readonly TgNode[], text: string): readonly TgNode[] => {
  if (text === '') return nodes
  const last = nodes.at(-1)
  return last?.kind === 'text' ? [...nodes.slice(0, -1), { kind: 'text', text: last.text + text }] : [...nodes, { kind: 'text', text }]
}

/**
 * Pure: Telegram HTML → typed nodes, so the bubble renders text and never markup.
 * Supports `<b>`, `<i>`, `<code>` and `&lt; &gt; &amp;`. Unknown or nested tags stay literal.
 */
export const parseTelegramHtml = (html: string): readonly TgNode[] => {
  const matches = [...html.matchAll(TAG)]
  const { nodes, end } = matches.reduce<{ readonly nodes: readonly TgNode[]; readonly end: number }>(
    (acc, m) => ({
      nodes: [...pushText(acc.nodes, decode(html.slice(acc.end, m.index))), { kind: m[1] as TgNode['kind'], text: decode(m[2]) }],
      end: m.index + m[0].length,
    }),
    { nodes: [], end: 0 },
  )
  return pushText(nodes, decode(html.slice(end)))
}
