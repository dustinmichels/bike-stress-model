<template>
  <div class="flowchart-container">
    <div ref="mermaidContainer" class="mermaid-wrapper"></div>
  </div>
</template>

<script setup lang="ts">
import type { BikeInfrastructureModel } from '@/types'
import { onMounted, ref, watch } from 'vue'

const props = defineProps<{
  modelConfig: BikeInfrastructureModel
}>()

const mermaidContainer = ref<HTMLElement>()

// Map speed limit categories to display labels
const getSpeedLimitDisplay = (category: string, displayLabel: string): string => {
  return displayLabel
}

// Generate the mermaid diagram syntax from model config
const generateMermaidSyntax = (): string => {
  const { separation_level, street_classification, speed_limit } = props.modelConfig

  // Build separation level box
  let sepContent = '<b>SEPARATION LEVEL</b><br/>────────────────'
  Object.entries(separation_level.categories).forEach(([key, value]) => {
    sepContent += `<br/>${value.displayLabel}: ${value.score}`
  })

  // Build street classification box
  let streetContent = '<b>STREET CLASSIFICATION</b><br/>────────────────'
  Object.entries(street_classification.categories).forEach(([key, value]) => {
    streetContent += `<br/>${value.displayLabel}: ${value.score}`
  })

  // Build speed limit box
  let speedContent = '<b>SPEED LIMIT</b><br/>────────────────'
  Object.entries(speed_limit.categories).forEach(([key, value]) => {
    speedContent += `<br/>${getSpeedLimitDisplay(key, value.displayLabel)}: ${value.score}`
  })

  // Build composite score box
  const compositeContent =
    '<b>COMPOSITE SCORE</b><br/>────────────────<br/>Weighted average of<br/>all three categories'

  return `
graph TB
    A["${sepContent}"]
    
    B["${streetContent}"]
    
    C["${speedContent}"]
    
    D["${compositeContent}"]
    
    A -->|"${separation_level.weight}% weight"| D
    B -->|"${street_classification.weight}% weight"| D
    C -->|"${speed_limit.weight}% weight"| D

    style A fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    style B fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    style C fill:#e8f5e9,stroke:#388e3c,stroke-width:3px
    style D fill:#fff3e0,stroke:#f57c00,stroke-width:4px
  `
}

// Initialize Mermaid and render the diagram
const renderMermaid = async () => {
  if (!mermaidContainer.value) return

  try {
    // Import mermaid dynamically
    const mermaid = (
      await import('https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs')
    ).default

    // Initialize mermaid
    mermaid.initialize({
      startOnLoad: false,
      theme: 'default',
      flowchart: {
        useMaxWidth: true,
        htmlLabels: true,
        curve: 'basis',
      },
    })

    // Generate the diagram syntax
    const syntax = generateMermaidSyntax()

    // Create a unique ID for this diagram
    const id = `mermaid-${Date.now()}`

    // Render the diagram
    const { svg } = await mermaid.render(id, syntax)

    // Insert the SVG into the container
    mermaidContainer.value.innerHTML = svg
  } catch (error) {
    console.error('Error rendering Mermaid diagram:', error)
    if (mermaidContainer.value) {
      mermaidContainer.value.innerHTML = '<p class="has-text-danger">Error rendering diagram</p>'
    }
  }
}

// Render on mount
onMounted(() => {
  renderMermaid()
})

// Re-render when model config changes
watch(() => props.modelConfig, renderMermaid, { deep: true })
</script>

<style scoped>
.flowchart-container {
  width: 100%;
  overflow-x: auto;
  padding: 1rem 0;
}

.mermaid-wrapper {
  display: flex;
  justify-content: center;
  min-height: 400px;
}

.mermaid-wrapper :deep(svg) {
  max-width: 100%;
  height: auto;
}
</style>
