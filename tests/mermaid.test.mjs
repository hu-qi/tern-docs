import assert from 'node:assert/strict'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'
import { createMarkdownRenderer } from 'vitepress'
import { escapeVueUnsafeTokens } from '../docs/.vitepress/escape-vue.mjs'
import { mermaidFence } from '../docs/.vitepress/mermaid.mjs'

const docsDir = fileURLToPath(new URL('../docs', import.meta.url))

const md = await createMarkdownRenderer(docsDir, {
  config: (instance) => {
    escapeVueUnsafeTokens(instance)
    mermaidFence(instance)
  },
})

const DIAGRAM = [
  'flowchart TB',
  '  subgraph Host["Host: session daemon"]',
  '    Worker["Worker thread per plugin<br/>host.luau"]',
  '  end',
  '  Worker <-->|"in: lens lines<br/>out: frames"| Loop',
].join('\n')

const sourceOf = (html) => {
  const match = /<Mermaid source="([^"]+)"/.exec(html)
  assert.ok(match, html)
  return decodeURIComponent(match[1])
}

test('rewrites mermaid fences into a Mermaid component', () => {
  const html = md.render('```mermaid\n' + DIAGRAM + '\n```\n')
  assert.match(html, /<Mermaid source="/)
  assert.ok(!html.includes('```mermaid'), html)
  assert.ok(!html.includes('language-mermaid'), html)
})

test('round-trips the diagram source without vue escaping', () => {
  const html = md.render('```mermaid\n' + DIAGRAM + '\n```\n')
  assert.equal(sourceOf(html), DIAGRAM)
  assert.ok(sourceOf(html).includes('<br/>'))
})

test('keeps braces in mermaid source instead of placeholder escaping', () => {
  const html = md.render('```mermaid\nflowchart LR\n  A["{x}"] --> B\n```\n')
  assert.ok(sourceOf(html).includes('{x}'), html)
})

test('leaves other fenced languages as code blocks', () => {
  const html = md.render('```lua\nlocal x = 1\n```\n')
  assert.ok(html.includes('language-lua'), html)
  assert.ok(!html.includes('<Mermaid'), html)
})