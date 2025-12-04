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

          <!-- Mermaid Flowchart -->
          <ModelFlowChart v-if="modelConfig" :model-config="modelConfig" />
        </div>
      </section>
      <footer class="modal-card-foot">
        <button class="button is-success" @click="exportGeojson">
          <span class="icon">
            <i class="fas fa-file-code"></i>
          </span>
          <span>Download GeoJSON</span>
        </button>
        <button class="button is-primary" @click="exportDiagram">Save Diagram</button>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { BikeInfrastructureModel, GeoJsonData } from '@/types'
import { onMounted, onUnmounted } from 'vue'
import ModelFlowChart from './ModelFlowChart.vue'

const props = defineProps<{
  isOpen: boolean
  modelConfig?: BikeInfrastructureModel | null
  geojsonData?: GeoJsonData | null
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

const exportGeojson = () => {
  if (!props.geojsonData) {
    alert('No GeoJSON data to export')
    return
  }

  try {
    // Convert GeoJSON object to formatted JSON string
    const geojsonString = JSON.stringify(props.geojsonData, null, 2)

    // Create a blob and download
    const blob = new Blob([geojsonString], { type: 'application/geo+json' })
    const url = URL.createObjectURL(blob)

    const link = document.createElement('a')
    link.href = url
    link.download = 'bike-infrastructure.geojson'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Error exporting GeoJSON:', error)
    alert('Error exporting GeoJSON. Check console for details.')
  }
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
