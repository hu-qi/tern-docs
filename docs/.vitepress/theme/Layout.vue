<script setup lang="ts">
import DefaultTheme from 'vitepress/theme'
import CopyPageButton from './CopyPageButton.vue'
import PrintButton from './PrintButton.vue'

const { Layout } = DefaultTheme
</script>

<template>
  <Layout>
    <template #doc-footer-before>
      <div class="vp-doc-actions">
        <CopyPageButton />
        <PrintButton />
      </div>
    </template>
  </Layout>
</template>