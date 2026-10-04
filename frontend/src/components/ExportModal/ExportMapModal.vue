<script setup lang="ts">
import { Check, FileCode, FileImage, Link, Share2, Workflow } from '@lucide/vue'
import type { BikeInfrastructureModel, GeoJsonData } from '@/types'
import { onMounted, onUnmounted, shallowRef } from 'vue'
import ModelFlowChart from './ModelFlowChart.vue'

const props = defineProps<{
  isOpen: boolean
  modelConfig?: BikeInfrastructureModel | null
  geojsonData?: GeoJsonData | null
}>()

const emit = defineEmits<{
  close: []
}>()

const isCopied = shallowRef(false)
let copyTimeout: ReturnType<typeof setTimeout> | null = null

const close = () => {
  isCopied.value = false
  if (copyTimeout) {
    clearTimeout(copyTimeout)
    copyTimeout = null
  }
  emit('close')
}

const copyLink = async () => {
  try {
    const url = window.location.href
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(url)
    } else {
      const textArea = document.createElement('textarea')
      textArea.value = url
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      textArea.style.top = '-999999px'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      document.execCommand('copy')
      textArea.remove()
    }
    isCopied.value = true
    if (copyTimeout) clearTimeout(copyTimeout)
    copyTimeout = setTimeout(() => {
      isCopied.value = false
    }, 2000)
  } catch (error) {
    console.error('Error copying link:', error)
    alert('Failed to copy link')
  }
}

const exportDiagram = () => {
  // Find the SVG element in the ModelFlowChart
  const svg = document.querySelector('.mermaid-wrapper svg') as SVGSVGElement
  if (!svg) {
    alert('No diagram to export')
    return
  }

  // Get SVG dimensions
  const bbox = svg.getBoundingClientRect()
  const width = bbox.width
  const height = bbox.height

  // Serialize the SVG
  const serializer = new XMLSerializer()
  const svgString = serializer.serializeToString(svg)

  // Create a canvas element
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    alert('Failed to create canvas context')
    return
  }

  // Set canvas size (with some scale for better quality)
  const scale = 2
  canvas.width = width * scale
  canvas.height = height * scale
  ctx.scale(scale, scale)

  // Create an image from SVG
  const img = new Image()
  const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' })
  const url = URL.createObjectURL(svgBlob)

  img.onload = () => {
    // Fill white background
    ctx.fillStyle = 'white'
    ctx.fillRect(0, 0, width, height)

    // Draw the SVG image onto the canvas
    ctx.drawImage(img, 0, 0, width, height)

    // Convert canvas to PNG blob
    canvas.toBlob((blob) => {
      if (!blob) {
        alert('Failed to create PNG')
        return
      }

      // Download the PNG
      const pngUrl = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = pngUrl
      link.download = 'bike-infrastructure-model.png'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      URL.revokeObjectURL(pngUrl)
      URL.revokeObjectURL(url)
    }, 'image/png')
  }

  img.onerror = () => {
    alert('Failed to load diagram for export')
    URL.revokeObjectURL(url)
  }

  img.src = url
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
  if (copyTimeout) clearTimeout(copyTimeout)
  document.removeEventListener('keydown', handleEscape)
})
</script>

<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal is-active">
      <div class="modal-background" @click="close"></div>
      <div class="modal-card large-modal">
        <header class="modal-card-head">
          <p class="modal-card-title is-flex is-align-items-center">
            <Share2 :size="20" class="mr-2" />
            <span>Share / Export</span>
          </p>
          <button class="delete" aria-label="close" @click="close"></button>
        </header>
        <section class="modal-card-body">
          <div class="content">
            <h3 class="title is-5 is-flex is-align-items-center">
              <Workflow :size="18" class="mr-2 has-text-info" />
              <span>Bike Infrastructure Scoring Model</span>
            </h3>

            <!-- Mermaid Flowchart -->
            <ModelFlowChart v-if="modelConfig" :model-config="modelConfig" />
          </div>
        </section>
        <footer class="modal-card-foot">
          <button class="button" :class="isCopied ? 'is-success' : 'is-info'" @click="copyLink">
            <span class="icon">
              <component :is="isCopied ? Check : Link" :size="16" />
            </span>
            <span>{{ isCopied ? 'Link Copied!' : 'Copy Link' }}</span>
          </button>
          <button class="button is-primary" @click="exportDiagram">
            <span class="icon">
              <FileImage :size="16" />
            </span>
            <span>Download Diagram (png)</span>
          </button>
          <button class="button is-success" @click="exportGeojson">
            <span class="icon">
              <FileCode :size="16" />
            </span>
            <span>Download Data (geojson)</span>
          </button>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

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

.modal-card-foot {
  gap: 1rem;
  flex-wrap: wrap;
}
</style>
