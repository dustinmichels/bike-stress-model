<template>
  <div class="container is-fluid main-container">
    <div class="columns top-row">
      <div class="column is-two-thirds">
        <MapComponent ref="mapRef" />
      </div>
      <div class="column is-one-third">
        <AboutComponent />
      </div>
    </div>
    <div class="columns bottom-row">
      <div class="column">
        <ModelComponent @weights-changed="handleWeightsChanged" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { percentagesToWeights } from '@/utils/scoreManager'
import { ref } from 'vue'
import AboutComponent from './components/AboutComponent.vue'
import MapComponent from './components/MapComponent.vue'
import ModelComponent from './components/ModelComponent.vue'

const mapRef = ref()

const handleWeightsChanged = (percentages: {
  separation_level: number
  speed: number
  busyness: number
}) => {
  // Convert percentages to normalized weights
  const weights = percentagesToWeights(percentages)

  // Update the map with new weights
  // This triggers recalculation of composite scores and map re-render
  mapRef.value?.setWeights(weights)
}
</script>

<style scoped>
.main-container {
  height: 100vh;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.top-row {
  flex: 3;
  margin: 0 !important;
}

.bottom-row {
  flex: 1;
  margin: 0 !important;
}

.column {
  padding: 0.25rem;
  display: flex;
}
</style>
