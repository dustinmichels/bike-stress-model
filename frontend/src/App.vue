<template>
  <div class="container is-fluid main-container">
    <div class="columns top-row">
      <div class="column is-two-thirds">
        <MapComponent
          :geojson-data="geojsonData"
          :model-config="modelConfig"
          :use-good-colors="useGoodColors"
          @toggle-colors="useGoodColors = !useGoodColors"
        />
      </div>
      <div class="column is-one-third right-column">
        <AboutComponent :cities="cities" v-model:currCity="currCity" />
        <ExportMap @open-modal="isExportModalOpen = true" />
      </div>
    </div>
    <div class="columns bottom-row">
      <div class="column">
        <ModelComponent
          :model-config="modelConfig"
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
    />

    <!-- Export Map Modal -->
    <ExportMapModal
      :is-open="isExportModalOpen"
      :model-config="modelConfig"
      :geojson-data="geojsonData"
      @close="isExportModalOpen = false"
    />
  </div>
</template>

<script setup lang="ts">
import { BIKE_INFRASTRUCTURE_MODEL } from '@/data/bikeData'
import type { BikeInfrastructureModel, GeoJsonData, ModelWeights } from '@/types'
import { onMounted, ref, watch } from 'vue'
import AboutComponent from './components/AboutComponent.vue'
import ExportMap from './components/ExportButtons.vue'
import ExportMapModal from './components/ExportModal/ExportMapModal.vue'
import MapComponent from './components/Map/Map.vue'
import ModelComponent from './components/ModelSliders.vue'
import SettingsModal from './components/SettingsModal.vue'

// Cities configuration
const cities = ref<string[]>(['Somerville', 'Cambridge', 'Everett'])
const currCity = ref<string>('Somerville')

// City to geojson file mapping
const cityFileMap: Record<string, string> = {
  Somerville: 'somerville_streets.geojson',
  Cambridge: 'cambridge_streets.geojson',
  Everett: 'everett_streets.geojson',
}

// State
const geojsonData = ref<GeoJsonData | null>(null)
const modelConfig = ref<BikeInfrastructureModel>(
  JSON.parse(JSON.stringify(BIKE_INFRASTRUCTURE_MODEL)),
)

const settingsDataField = ref<string | null>(null)
const useGoodColors = ref(true)
const isExportModalOpen = ref(false)

// Load GeoJSON data for a specific city
const loadGeoJsonForCity = async (city: string) => {
  try {
    const fileName = cityFileMap[city]
    if (!fileName) {
      console.error(`No geojson file configured for city: ${city}`)
      return
    }
    const response = await fetch(import.meta.env.BASE_URL + fileName)
    if (!response.ok) throw new Error(`HTTP error: ${response.status}`)
    const data = await response.json()
    geojsonData.value = data
  } catch (e) {
    console.error(`Error loading GeoJSON for ${city}:`, e)
  }
}

// Load GeoJSON data on mount
onMounted(() => {
  loadGeoJsonForCity(currCity.value)
})

// Watch for city changes and reload geojson
watch(currCity, (newCity) => {
  loadGeoJsonForCity(newCity)
})

// Handle weight changes from ModelComponent
const handleWeightsChanged = (weights: ModelWeights) => {
  // Update weights in modelConfig
  modelConfig.value.separation_level.weight = weights.separation_level
  modelConfig.value.speed_limit.weight = weights.speed
  modelConfig.value.street_classification.weight = weights.busyness
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

.right-column {
  flex-direction: column;
  gap: 0.25rem;
}
</style>
