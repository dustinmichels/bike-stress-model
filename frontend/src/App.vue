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
        <ModelComponent
          @weights-changed="handleWeightsChanged"
          @open-settings="handleOpenSettings"
        />
      </div>
    </div>

    <!-- Settings Modal -->
    <div v-if="settingsDataField" class="modal is-active">
      <div class="modal-background" @click="settingsDataField = null"></div>
      <div class="modal-card">
        <header class="modal-card-head">
          <p class="modal-card-title">Settings: {{ getParameterDisplayName(settingsDataField) }}</p>
          <button class="delete" aria-label="close" @click="settingsDataField = null"></button>
        </header>
        <section class="modal-card-body">
          <div v-if="currentParameterData">
            <p class="mb-4">{{ currentParameterData.notes }}</p>

            <h4 class="title is-6">Categories:</h4>
            <div
              v-for="(category, key) in currentParameterData.categories"
              :key="key"
              class="box mb-3"
            >
              <div class="is-flex is-justify-content-space-between is-align-items-center mb-2">
                <strong class="is-capitalized">{{ formatCategoryName(key) }}</strong>
                <span class="tag is-info">Score: {{ category.score }}</span>
              </div>
              <p class="is-size-7">{{ category.notes }}</p>
              <img
                v-if="category.img"
                :src="category.img"
                alt=""
                class="mt-2"
                style="max-width: 100%; height: auto"
              />
            </div>

            <a
              v-if="currentParameterData.link"
              :href="currentParameterData.link"
              target="_blank"
              class="button is-link is-small mt-4"
            >
              <span class="icon is-small">
                <i class="fas fa-external-link-alt"></i>
              </span>
              <span>Learn More on OpenStreetMap Wiki</span>
            </a>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { BIKE_INFRASTRUCTURE_DATA } from '@/data/bikeData'
import { percentagesToWeights } from '@/utils/scoreManager'
import { computed, ref } from 'vue'
import AboutComponent from './components/AboutComponent.vue'
import MapComponent from './components/MapComponent.vue'
import ModelComponent from './components/ModelComponent.vue'

const mapRef = ref()
const settingsDataField = ref<string | null>(null)

// Computed property to get the parameter data for the current settings view
const currentParameterData = computed(() => {
  if (!settingsDataField.value) return null
  return BIKE_INFRASTRUCTURE_DATA[settingsDataField.value as keyof typeof BIKE_INFRASTRUCTURE_DATA]
})

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

// Handle opening settings modal
const handleOpenSettings = (dataField: string) => {
  settingsDataField.value = dataField
}

// Helper function to get display name for parameter
const getParameterDisplayName = (dataField: string): string => {
  const displayNames: Record<string, string> = {
    separation_level: 'Separation Level',
    speed_limit: 'Speed Limit',
    street_classification: 'Street Classification (Busyness)',
  }
  return displayNames[dataField] || dataField
}

// Helper function to format category names nicely
const formatCategoryName = (key: string): string => {
  return key.replace(/_/g, ' ').replace(/-/g, ' ')
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

.modal-card-body .box {
  background-color: #f5f5f5;
}

/* Ensure modal appears above map */
.modal {
  z-index: 99999 !important;
}

.modal-background {
  z-index: 99998 !important;
}

.modal-card {
  z-index: 100000 !important;
}
</style>
