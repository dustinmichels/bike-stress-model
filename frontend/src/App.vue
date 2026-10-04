<script setup lang="ts">
import type { ColorMode } from '@/types'
import { useBikeModel } from '@/composables/useBikeModel'
import { useCitySelection } from '@/composables/useCitySelection'
import { defineAsyncComponent, shallowRef } from 'vue'
import AboutComponent from './components/AboutComponent.vue'
import ExportButtons from './components/ExportButtons.vue'
import MapComponent from './components/Map/Map.vue'
import ModelSliders from './components/ModelSliders.vue'
import SettingsModal from './components/SettingsModal.vue'

// Lazy-load heavy ExportMapModal containing mermaid to keep initial bundle lightweight
const ExportMapModal = defineAsyncComponent(
  () => import('./components/ExportModal/ExportMapModal.vue'),
)

// City selection & URL state management
const { cities, currCity } = useCitySelection()

// UI display state
const settingsDataField = shallowRef<string | null>(null)
const colorMode = shallowRef<ColorMode>('safety')
const isExportModalOpen = shallowRef(false)

// Bike model configuration, weights, and scored GeoJSON dataset
const {
  modelConfig,
  geojsonData,
  enrichedGeoJson,
  loading,
  error,
  handleWeightsChanged,
  handleUpdateScore,
} = useBikeModel({
  city: currCity,
  colorMode,
})

const handleOpenSettings = (dataField: string) => {
  settingsDataField.value = dataField
}
</script>

<template>
  <div class="container is-fluid main-container">
    <div class="columns is-multiline top-row">
      <div class="column is-two-thirds-tablet is-full-mobile map-column">
        <MapComponent
          :geojson-data="enrichedGeoJson"
          :raw-geojson-data="geojsonData"
          :model-config="modelConfig"
          :color-mode="colorMode"
          :loading="loading"
          :error="error"
          @update:color-mode="colorMode = $event"
        />
      </div>
      <div class="column is-one-third-tablet is-full-mobile right-column">
        <AboutComponent :cities="cities" v-model:curr-city="currCity" />
        <ExportButtons @open-modal="isExportModalOpen = true" />
      </div>
    </div>
    <div class="columns bottom-row">
      <div class="column">
        <ModelSliders
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

    <!-- Export Map Modal (lazy loaded) -->
    <ExportMapModal
      v-if="isExportModalOpen"
      :is-open="isExportModalOpen"
      :model-config="modelConfig"
      :geojson-data="enrichedGeoJson"
      @close="isExportModalOpen = false"
    />
  </div>
</template>

<style scoped>
.main-container {
  height: 100vh;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  overflow: auto;
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

/* Mobile-specific styles */
@media screen and (max-width: 768px) {
  .main-container {
    height: auto;
    min-height: 100vh;
    overflow: visible;
  }

  .top-row {
    flex: none;
    display: flex;
    flex-direction: column;
  }

  .bottom-row {
    flex: none;
  }

  .map-column {
    min-height: 50vh;
    max-height: 50vh;
    order: 1;
  }

  .right-column {
    order: 2;
    height: auto;
  }

  .column {
    height: auto;
  }
}

/* Tablet adjustments */
@media screen and (min-width: 769px) and (max-width: 1023px) {
  .map-column {
    min-height: 60vh;
  }
}
</style>
