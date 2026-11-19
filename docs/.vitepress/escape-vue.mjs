/**
 * Make the upstream mdBook pages safe to compile as Vue SFC templates.
 *
 * VitePress renders Markdown into a Vue template, so three constructs that are
 * plain text upstream would be interpreted by Vue:
 *
 * - `{{ ... }}` (Vue interpolation) appears in prose and inline code,
 * - `<name>` placeholders such as `<config>` or `<builder>` look like tags,
 * - inline `&` sequences.
 *
 * The rule below escapes those characters in text and inline-code tokens only,
 * so fenced code blocks, links, anchors and real HTML (figure/img/div …) keep
 * their exact rendering.
 */
const ALLOWED_TAGS = new Set([
  'a', 'abbr', 'b', 'blockquote', 'br', 'code', 'dd', 'del', 'details', 'div',
  'dl', 'dt', 'em', 'figcaption', 'figure', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'hr', 'i', 'img', 'ins', 'kbd', 'li', 'mark', 'ol', 'p', 'pre', 's', 'small',
  'span', 'strong', 'sub', 'summary', 'sup', 'table', 'tbody', 'td', 'th',
  'thead', 'tr', 'u', 'ul', 'wbr',
])

const escapeHtml = (text) =>
  text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\{/g, '&#123;')
    .replace(/\}/g, '&#125;')

export function escapeVueUnsafeTokens(md) {
  // Custom heading ids (`## Heading {#id}`) are applied on the Markdown source
  // before inline parsing, so VitePress's own anchor plugin never sees the
  // `{#id}` markup (it would otherwise leak into the permalink label). The
  // ordinal of each heading is recorded so the id lands on the right one.
  md.core.ruler.before('block', 'heading-ids-strip', (state) => {
    const ids = new Map()
    let ordinal = 0
    let inFence = false
    state.src = state.src
      .split('\n')
      .map((line) => {
        if (line.startsWith('```')) {
          inFence = !inFence
          return line
        }
        if (inFence) return line
        if (!/^#{1,6}[ \t]+/.test(line)) return line
        const current = ordinal++
        const match = /^(#{1,6}[ \t]+.*?)[ \t]*\{#([^}]+)\}[ \t]*$/.exec(line)
        if (!match) return line
        ids.set(current, match[2])
        return match[1]
      })
      .join('\n')
    state.env.headingIds = ids
  })

  const applyHeadingIds = (state) => {
    const ids = state.env.headingIds || new Map()
    let ordinal = 0
    for (const token of state.tokens) {
      if (token.type !== 'heading_open') continue
      const id = ids.get(ordinal++)
      if (id) token.attrSet('id', id)
    }
  }

  // Must run before markdown-it-anchor, which uses an existing `id` attribute
  // for the heading and its permalink href.
  try {
    md.core.ruler.before('anchor', 'heading-ids-apply', applyHeadingIds)
  } catch {
    md.core.ruler.push('heading-ids-apply', applyHeadingIds)
  }

  md.core.ruler.push('escape-vue-unsafe-tokens', (state) => {
    for (const token of state.tokens) {
      if (token.type === 'html_block' && token.content.trimStart().startsWith('<')) {
        if (token.content.startsWith('<!--')) continue
        const name = /^<\s*([a-zA-Z][\w-]*)/.exec(token.content.trimStart())?.[1]?.toLowerCase()
        if (name && !ALLOWED_TAGS.has(name)) {
          token.content = escapeHtml(token.content)
        }
        continue
      }
      if (token.type !== 'inline' || !token.children) continue
      for (const child of token.children) {
        if (child.type === 'text' && /[<{]/.test(child.content)) {
          child.type = 'html_inline'
          child.content = escapeHtml(child.content)
        } else if (child.type === 'code_inline' && /[<{&]/.test(child.content)) {
          child.type = 'html_inline'
          child.content = `<code>${escapeHtml(child.content)}</code>`
        } else if (child.type === 'html_inline' && child.content.startsWith('<')) {
          if (child.content.startsWith('<!--')) continue
          const name = /^<\/?\s*([a-zA-Z][\w-]*)/.exec(child.content)?.[1]?.toLowerCase()
          if (name && !ALLOWED_TAGS.has(name) && !name.startsWith('v-')) {
            child.type = 'html_inline'
            child.content = escapeHtml(child.content)
          }
        }
      }
    }
  })
}