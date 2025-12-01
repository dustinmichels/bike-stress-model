<template>
  <div class="container is-fluid main-container">
    <div class="columns top-row">
      <div class="column is-two-thirds">
        <MapComponent
          :geojson-data="geojsonData"
          :model-config="modelConfig"
          :model-weights="modelWeights"
          :use-good-colors="useGoodColors"
          @toggle-colors="useGoodColors = !useGoodColors"
        />
      </div>
      <div class="column is-one-third">
        <AboutComponent />
      </div>
    </div>
    <div class="columns bottom-row">
      <div class="column">
        <ModelComponent
          :weights="modelWeights"
          @weights-changed="handleWeightsChanged"
          @open-settings="handleOpenSettings"
        />
      </div>
    </div>

    <!-- Settings Modal -->
    <SettingsModal
      :data-field="settingsDataField"
      :model-config="modelConfig"
      @close="settingsDataField = null"
      @update-score="handleUpdateScore"
      @update-default-category="handleUpdateDefaultCategory"
    />
  </div>
</template>

<script setup lang="ts">
import { BIKE_INFRASTRUCTURE_MODEL } from '@/data/bikeData'
import type { BikeInfrastructureModel, GeoJsonData, ModelWeights } from '@/types'
import { onMounted, ref } from 'vue'
import AboutComponent from './components/AboutComponent.vue'
import MapComponent from './components/Map/Map.vue'
import ModelComponent from './components/ModelComponent.vue'
import SettingsModal from './components/SettingsModal.vue'

// State
const geojsonData = ref<GeoJsonData | null>(null)
const modelConfig = ref<BikeInfrastructureModel>(
  JSON.parse(JSON.stringify(BIKE_INFRASTRUCTURE_MODEL)),
)

// Extract weights from the model
const modelWeights = ref<ModelWeights>({
  separation_level: BIKE_INFRASTRUCTURE_MODEL.separation_level.weight,
  speed: BIKE_INFRASTRUCTURE_MODEL.speed_limit.weight,
  busyness: BIKE_INFRASTRUCTURE_MODEL.street_classification.weight,
})

const settingsDataField = ref<string | null>(null)
const useGoodColors = ref(true)

// Load GeoJSON data on mount
onMounted(async () => {
  try {
    const response = await fetch(new URL('somerville_streets.geojson', import.meta.env.BASE_URL))
    // const response = await fetch('/cambridge_streets.geojson')
    if (!response.ok) throw new Error(`HTTP error: ${response.status}`)
    const data = await response.json()
    geojsonData.value = data
  } catch (e) {
    console.error('Error loading GeoJSON:', e)
  }
})

// Handle weight changes from ModelComponent
const handleWeightsChanged = (weights: ModelWeights) => {
  modelWeights.value = { ...weights }
}

// Handle opening settings modal
const handleOpenSettings = (dataField: string) => {
  settingsDataField.value = dataField
}

// Handle score updates from SettingsModal
const handleUpdateScore = (field: string, category: string, score: number) => {
  const fieldConfig = modelConfig.value[field as keyof BikeInfrastructureModel]
  if (fieldConfig?.categories[category]) {
    fieldConfig.categories[category].score = score
  }
}

// Handle default category updates from SettingsModal
const handleUpdateDefaultCategory = (field: string, defaultCategory: string | number) => {
  if (modelConfig.value[field as keyof BikeInfrastructureModel]) {
    modelConfig.value[field as keyof BikeInfrastructureModel].defaultCategory = defaultCategory
  }
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
