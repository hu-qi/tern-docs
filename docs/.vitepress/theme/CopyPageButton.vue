<script setup lang="ts">
import { computed, ref } from 'vue'
import { useData } from 'vitepress'

const { page, site } = useData()
const state = ref<'idle' | 'copied' | 'failed'>('idle')

const zh = computed(() => page.value.relativePath.startsWith('zh/'))
const labels = computed(() =>
  zh.value
    ? { idle: '复制本页', copied: '已复制', failed: '打开原文' }
    : { idle: 'Copy page', copied: 'Copied', failed: 'Open source' },
)

const markdownHref = computed(() => {
  const base = site.value.base || '/'
  return `${base}${page.value.relativePath}`
})

async function copyPage() {
  try {
    const response = await fetch(markdownHref.value)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const text = await response.text()
    await navigator.clipboard.writeText(text)
    state.value = 'copied'
    window.setTimeout(() => (state.value = 'idle'), 2000)
  } catch {
    state.value = 'failed'
    window.open(markdownHref.value, '_blank', 'noopener')
  }
}
</script>

<template>
  <button type="button" class="vp-doc-action" @click="copyPage">
    {{ labels[state] }}
  </button>
</template>