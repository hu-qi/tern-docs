import assert from 'node:assert/strict'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'
import { createMarkdownRenderer } from 'vitepress'
import { escapeVueUnsafeTokens } from '../docs/.vitepress/escape-vue.mjs'

const docsDir = fileURLToPath(new URL('../docs', import.meta.url))

const md = await createMarkdownRenderer(docsDir, {
  config: (instance) => escapeVueUnsafeTokens(instance),
})

const render = (src) => md.render(src)

test('escapes Vue interpolation in prose', () => {
  const html = render('The value {{ plugin.name }} is injected.')
  assert.ok(html.includes('&#123;&#123; plugin.name &#125;&#125;'), html)
  assert.ok(!html.includes('{{ plugin.name }}'), html)
})

test('escapes angle-bracket placeholders in prose', () => {
  const html = render('Place it in <config> next to <builder>.')
  assert.ok(html.includes('&lt;config&gt;'), html)
  assert.ok(html.includes('&lt;builder&gt;'), html)
})

test('applies custom heading ids without leaking the markup', () => {
  const html = render('## Custom heading {#my-id}\n')
  assert.match(html, /<h2[^>]*\bid="my-id"/)
  assert.ok(html.includes('href="#my-id"'), html)
  assert.ok(!html.includes('{#my-id}'), html)
})

test('leaves fenced code blocks untouched', () => {
  const source = '```lua\nlocal x = "{{ plugin.name }}" -- <Tag>\n```\n'
  const html = render(source)
  assert.ok(html.includes('{{ plugin.name }}'), html)
  assert.ok(!html.includes('&#123;'), html)
  // Shiki escapes `<` as `&#x3C;`; the plugin must not escape it a second time.
  assert.ok(html.includes('&#x3C;Tag>'), html)
  assert.ok(!html.includes('&amp;'), html)
})

test('escapes Vue syntax inside inline code', () => {
  const html = render('Use `{{ value }}` here.')
  assert.ok(html.includes('&#123;&#123; value &#125;&#125;'), html)
  assert.ok(!html.includes('{{ value }}'), html)
})

test('keeps allowed raw HTML intact', () => {
  const html = render('<figure><img src="a.png" alt="x"><figcaption>x</figcaption></figure>\n')
  assert.ok(html.includes('<figure>'), html)
  assert.ok(html.includes('<img src="a.png"'), html)
})