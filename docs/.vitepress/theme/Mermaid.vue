<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

const props = defineProps<{ source: string }>()

const host = ref<HTMLElement | null>(null)
let counter = 0

async function render() {
  if (!host.value) return
  const source = decodeURIComponent(props.source)
  const { default: mermaid } = await import('mermaid')
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: 'loose',
    theme: document.documentElement.classList.contains('dark') ? 'dark' : 'default',
    flowchart: { htmlLabels: true },
  })
  const id = `vp-mermaid-${Date.now()}-${counter++}`
  try {
    const { svg } = await mermaid.render(id, source)
    if (host.value) host.value.innerHTML = svg
  } catch (error) {
    host.value.textContent = source
    console.error('[mermaid] render failed', error)
  }
}

onMounted(render)
watch(() => props.source, render)
</script>

<template>
  <div ref="host" class="vp-mermaid" />
</template>