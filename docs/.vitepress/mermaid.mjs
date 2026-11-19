/**
 * Rewrite ```mermaid fences into <Mermaid source="..." /> components.
 *
 * The diagram source is passed as a URL-encoded prop instead of being inlined
 * into the template: the source contains `{}`, `<br/>` and quotes that the
 * `escapeVueUnsafeTokens` rule (and the Vue template compiler) would otherwise
 * reinterpret. `encodeURIComponent` leaves only URL-safe characters, so the
 * value round-trips through a double-quoted HTML attribute without ambiguity.
 *
 * Register this rule *after* `escape-vue-unsafe-tokens`, otherwise the
 * generated `<Mermaid>` block would itself be escaped.
 */
const MERMAID_LANG = 'mermaid'

export function mermaidFence(md) {
  md.core.ruler.after('escape-vue-unsafe-tokens', 'mermaid-fence', (state) => {
    for (const token of state.tokens) {
      if (token.type !== 'fence') continue
      const info = (token.info || '').trim().split(/\s+/)[0]
      if (info !== MERMAID_LANG) continue
      const source = token.content.replace(/\s+$/, '')
      token.type = 'html_block'
      token.content = `<Mermaid source="${encodeURIComponent(source)}" />\n`
    }
  })
}