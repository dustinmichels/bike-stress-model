<template>
  <div class="modal" :class="{ 'is-active': isOpen }">
    <div class="modal-background" @click="close"></div>
    <div class="modal-card large-modal">
      <header class="modal-card-head">
        <p class="modal-card-title">Export Map</p>
        <button class="delete" aria-label="close" @click="close"></button>
      </header>
      <section class="modal-card-body">
        <div class="content">
          <h3 class="title is-5">Bike Infrastructure Scoring Model</h3>
          <p class="subtitle is-6">
            This flowchart shows how different infrastructure categories are weighted to calculate
            the composite score.
          </p>

          <!-- Mermaid Flowchart -->
          <ModelFlowChart v-if="modelConfig" :model-config="modelConfig" />

          <div class="notification is-info is-light mt-4">
            <p>
              <strong>How to use this diagram:</strong><br />
              • Each box shows a scoring category with its possible values<br />
              • The arrows show how categories are weighted to create the composite score<br />
              • Lower scores (closer to 0) indicate better bike infrastructure
            </p>
          </div>
        </div>
      </section>
      <footer class="modal-card-foot">
        <button class="button" @click="close">Close</button>
        <button class="button is-primary" @click="exportDiagram">Export Diagram</button>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { BikeInfrastructureModel } from '@/types'
import { onMounted, onUnmounted } from 'vue'
import ModelFlowChart from './ModelFlowChart.vue'

const props = defineProps<{
  isOpen: boolean
  modelConfig?: BikeInfrastructureModel
}>()

const emit = defineEmits<{
  close: []
}>()

const close = () => {
  emit('close')
}

const exportDiagram = () => {
  // Find the SVG element in the ModelFlowChart
  const svg = document.querySelector('.mermaid-wrapper svg')
  if (!svg) {
    alert('No diagram to export')
    return
  }

  // Serialize the SVG
  const serializer = new XMLSerializer()
  const svgString = serializer.serializeToString(svg)

  // Create a blob and download
  const blob = new Blob([svgString], { type: 'image/svg+xml' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = 'bike-infrastructure-model.svg'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  URL.revokeObjectURL(url)
}

const handleEscape = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && props.isOpen) {
    close()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleEscape)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape)
})
</script>

<style scoped>
.modal {
  z-index: 9999;
}

.large-modal {
  max-width: 1000px;
  width: 90vw;
}

.modal-card-body {
  max-height: 70vh;
  overflow-y: auto;
}
</style>
