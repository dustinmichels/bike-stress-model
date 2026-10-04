<script setup lang="ts">
import { BookOpen, Share2 } from '@lucide/vue'

const emit = defineEmits<{
  openExport: []
  openAbout: []
}>()
</script>

<template>
  <div class="box export-map-container">
    <button type="button" class="button is-primary is-fullwidth" @click="emit('openExport')">
      <span class="icon">
        <Share2 :size="16" />
      </span>
      <span>Share / Export</span>
    </button>
    <button type="button" class="button is-info is-fullwidth mt-2" @click="emit('openAbout')">
      <span class="icon">
        <BookOpen :size="16" />
      </span>
      <span>About</span>
    </button>
  </div>
</template>

<style scoped>
.export-map-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: center;
}

@media screen and (max-width: 768px) {
  .export-map-container {
    height: auto;
    min-height: auto;
  }
}
</style>
