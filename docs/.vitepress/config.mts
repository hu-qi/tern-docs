import fs from 'node:fs'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitepress'
import { escapeVueUnsafeTokens } from './escape-vue.mjs'
import { mermaidFence } from './mermaid.mjs'

const repoRoot = fileURLToPath(new URL('../..', import.meta.url))
const siteMap = JSON.parse(fs.readFileSync(`${repoRoot}site-map.json`, 'utf-8'))
const SITE_BASE = '/tern-docs/'

const sectionTitlesZh: Record<string, string> = {
  Overview: '总览',
  Concepts: '核心概念',
  Guides: '开发指南',
  Elements: '元素',
  Styles: '样式',
  'Surface Protocol': 'Surface 协议',
  Examples: '示例',
  Scripts: '脚本 API',
  Reference: '参考资料',
}

function firstHeading(file: string): string | undefined {
  try {
    const line = fs
      .readFileSync(file, 'utf-8')
      .split('\n')
      .find((candidate) => candidate.startsWith('# '))
    return line?.replace(/^#\s+/, '').replace(/\s*\{#[^}]+\}\s*$/, '').trim()
  } catch {
    return undefined
  }
}

type Page = { path: string; title: string }

function pageTitle(page: Page, lang: 'en' | 'zh'): string {
  if (lang === 'en') return page.title
  return firstHeading(`${repoRoot}docs/zh/${page.path}`) ?? page.title
}

function buildSidebar(lang: 'en' | 'zh') {
  const prefix = lang === 'zh' ? '/zh/' : '/'
  return siteMap.sections.map((section: { title: string; pages: Page[] }) => ({
    text: lang === 'zh' ? (sectionTitlesZh[section.title] ?? section.title) : section.title,
    collapsed: false,
    items: section.pages.map((page: Page) => ({
      text: pageTitle(page, lang),
      link: `${prefix}${page.path.replace(/\.md$/, '').replace(/(^|\/)index$/, '$1')}`,
    })),
  }))
}

export default defineConfig({
  base: SITE_BASE,
  srcExclude: ['issue-1/**', 'issue-3/**', 'issue-5/**'],
  cleanUrls: true,
  lastUpdated: false,
  title: 'Tern Plugin SDK',
  description: 'Tern Plugin SDK 文档 / Documentation — English & 简体中文',
  head: [['meta', { name: 'theme-color', content: '#08090d' }]],
  transformHead({ pageData }) {
    const relativePath = pageData.relativePath
    if (!relativePath || !relativePath.endsWith('.md') || relativePath === '404.md') return []
    return [
      [
        'link',
        {
          rel: 'alternate',
          type: 'text/markdown',
          href: `${SITE_BASE}${relativePath}`,
        },
      ],
    ]
  },
  markdown: {
    config(md) {
      escapeVueUnsafeTokens(md)
      mermaidFence(md)
    },
  },
  locales: {
    root: { label: 'English', lang: 'en' },
    zh: {
      label: '简体中文',
      lang: 'zh-CN',
      description: 'Tern 插件 SDK 文档',
      themeConfig: {
        nav: [{ text: '总览', link: '/zh/' }],
        sidebar: buildSidebar('zh'),
        outline: { label: '本页目录', level: [2, 3] },
        docFooter: { prev: '上一页', next: '下一页' },
        returnToTopLabel: '回到顶部',
        langMenuLabel: '切换语言',
        darkModeSwitchLabel: '外观',
        sidebarMenuLabel: '目录',
        lastUpdatedText: '最后更新',
      },
    },
  },
  themeConfig: {
    nav: [{ text: 'Overview', link: '/' }],
    sidebar: buildSidebar('en'),
    outline: { label: 'On this page', level: [2, 3] },
    socialLinks: [{ icon: 'github', link: 'https://github.com/hu-qi/tern-docs' }],
    search: { provider: 'local' },
  },
})