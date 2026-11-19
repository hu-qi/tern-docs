<script setup lang="ts">
import { computed } from 'vue'
import { useData } from 'vitepress'

const { page } = useData()
const label = computed(() => (page.value.relativePath.startsWith('zh/') ? '打印本页' : 'Print page'))

function printPage() {
  window.print()
}
</script>

<template>
  <button type="button" class="vp-doc-action" @click="printPage">
    {{ label }}
  </button>
</template>