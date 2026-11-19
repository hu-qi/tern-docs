import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'

const read = (path) => readFileSync(fileURLToPath(new URL(path, import.meta.url)), 'utf-8')

test('print styles hide chrome and avoid page breaks inside blocks', () => {
  const css = read('../docs/.vitepress/theme/custom.css')
  assert.match(css, /@media print/)
  for (const selector of ['.VPNav', '.VPSidebar', '.VPLocalNav', '.VPDocAside', '.VPFooter']) {
    assert.ok(css.includes(selector), selector)
  }
  assert.match(css, /pre,[\s\S]*break-inside: avoid/)
})

test('layout exposes copy and print actions before the doc footer', () => {
  const layout = read('../docs/.vitepress/theme/Layout.vue')
  assert.match(layout, /#doc-footer-before/)
  assert.match(layout, /CopyPageButton/)
  assert.match(layout, /PrintButton/)
})

test('copy button reads the per-language markdown source', () => {
  const button = read('../docs/.vitepress/theme/CopyPageButton.vue')
  assert.match(button, /relativePath/)
  assert.match(button, /navigator\.clipboard\.writeText/)
  assert.match(button, /window\.open/)
})

test('config injects markdown alternate links per page', () => {
  const config = read('../docs/.vitepress/config.mts')
  assert.match(config, /transformHead/)
  assert.match(config, /rel: 'alternate'/)
  assert.match(config, /type: 'text\/markdown'/)
  assert.match(config, /mermaidFence/)
})