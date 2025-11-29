<template>
  <div class="box map-component">
    <div class="notification is-danger is-light" v-if="error">
      {{ error }}
    </div>

    <div class="notification is-info is-light" v-if="loading">Loading map data...</div>

    <div ref="mapContainer" class="map-container"></div>

    <!-- Legend -->
    <div class="legend">
      <div class="legend-title">Composite Score</div>
      <div class="legend-gradient"></div>
      <div class="legend-labels">
        <span>0 (Worst)</span>
        <span>10 (Best)</span>
      </div>
    </div>

    <!-- Score Controls (optional - you can show/hide this) -->
    <div class="score-controls" v-if="showControls">
      <div class="score-control-title">Adjust Weights</div>
      <div class="weight-slider">
        <label>Max Speed Score: {{ weights.maxspeed_int_score.toFixed(1) }}</label>
        <input
          type="range"
          min="0"
          max="2"
          step="0.1"
          v-model.number="weights.maxspeed_int_score"
          @input="onWeightsChange"
        />
      </div>
      <div class="weight-slider">
        <label>Separation Level Score: {{ weights.separation_level_score.toFixed(1) }}</label>
        <input
          type="range"
          min="0"
          max="2"
          step="0.1"
          v-model.number="weights.separation_level_score"
          @input="onWeightsChange"
        />
      </div>
      <div class="weight-slider">
        <label
          >Street Classification Score: {{ weights.street_classification_score.toFixed(1) }}</label
        >
        <input
          type="range"
          min="0"
          max="2"
          step="0.1"
          v-model.number="weights.street_classification_score"
          @input="onWeightsChange"
        />
      </div>
      <div class="weight-slider">
        <label>Lanes Score: {{ weights.lanes_int_score.toFixed(1) }}</label>
        <input
          type="range"
          min="0"
          max="2"
          step="0.1"
          v-model.number="weights.lanes_int_score"
          @input="onWeightsChange"
        />
      </div>
      <button class="button is-small" @click="resetWeights">Reset Weights</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  type GeoJsonData,
  type ScoreWeights,
  defaultWeights,
  recalculateAllScores,
} from '@/utils/scoreManager'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { onMounted, onUnmounted, reactive, ref } from 'vue'

// Fix for default marker icons in Leaflet with bundlers
import iconRetina from 'leaflet/dist/images/marker-icon-2x.png'
import icon from 'leaflet/dist/images/marker-icon.png'
import iconShadow from 'leaflet/dist/images/marker-shadow.png'

const DefaultIcon = L.icon({
  iconUrl: icon,
  iconRetinaUrl: iconRetina,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})
L.Marker.prototype.options.icon = DefaultIcon

// Props
interface Props {
  showControls?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showControls: false,
})

// Refs
const mapContainer = ref<HTMLElement | null>(null)
const error = ref('')
const loading = ref(true)

// GeoJSON data storage
const originalGeoJson = ref<GeoJsonData | null>(null) // Preserve original from server
const currentGeoJson = ref<GeoJsonData | null>(null) // Working copy with recalculated scores

// Score weights (reactive)
const weights = reactive<ScoreWeights>({ ...defaultWeights })

// Leaflet instances
let map: L.Map | null = null
let geojsonLayer: L.GeoJSON | null = null

// Color scale function: 0 (red) to 10 (green)
const getColorForScore = (score: number): string => {
  // Clamp score between 0 and 10
  const clampedScore = Math.max(0, Math.min(10, score))

  // Normalize to 0-1 range
  const normalized = clampedScore / 10

  // Color gradient from red (bad) to yellow (medium) to green (good)
  if (normalized < 0.5) {
    // Red to Yellow (0 to 0.5)
    const ratio = normalized * 2
    const r = 255
    const g = Math.round(ratio * 255)
    const b = 0
    return `rgb(${r}, ${g}, ${b})`
  } else {
    // Yellow to Green (0.5 to 1)
    const ratio = (normalized - 0.5) * 2
    const r = Math.round(255 * (1 - ratio))
    const g = 255
    const b = 0
    return `rgb(${r}, ${g}, ${b})`
  }
}

// Initialize map and load GeoJSON
onMounted(async () => {
  if (mapContainer.value) {
    // Initialize map centered on Somerville, MA with more zoom
    map = L.map(mapContainer.value).setView([42.3876, -71.0995], 15)

    const CartoDB_Positron = L.tileLayer(
      'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
      {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 30,
      },
    )

    CartoDB_Positron.addTo(map)

    // Load the GeoJSON file
    await loadGeoJson()
  }
})

// Cleanup on unmount
onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})

// Load GeoJSON from public directory
const loadGeoJson = async () => {
  try {
    loading.value = true
    error.value = ''

    const response = await fetch('/somerville_streets.geojson')
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()

    // Store original data
    originalGeoJson.value = data

    // Calculate initial composite scores and store in working copy
    currentGeoJson.value = recalculateAllScores(data, weights)

    // Add to map
    addGeoJsonToMap(currentGeoJson.value)
  } catch (e) {
    error.value = `Error loading GeoJSON: ${e instanceof Error ? e.message : 'Unknown error'}`
  } finally {
    loading.value = false
  }
}

// Add GeoJSON to map
const addGeoJsonToMap = (geojsonData: GeoJsonData) => {
  if (!map) return

  try {
    // Remove existing GeoJSON layer if any
    if (geojsonLayer) {
      map.removeLayer(geojsonLayer)
    }

    // Add new GeoJSON layer
    geojsonLayer = L.geoJSON(geojsonData, {
      onEachFeature: (feature, layer) => {
        // Add popup with properties
        if (feature.properties) {
          const popupContent = Object.entries(feature.properties)
            .map(([key, value]) => {
              // Format numbers to 2 decimal places
              const formattedValue = typeof value === 'number' ? value.toFixed(2) : value
              return `<strong>${key}:</strong> ${formattedValue}`
            })
            .join('<br>')
          layer.bindPopup(popupContent)
        }
      },
      style: (feature) => {
        // Get composite_score from properties
        const compositeScore = feature?.properties?.composite_score ?? 5 // Default to middle if missing

        return {
          color: getColorForScore(compositeScore),
          weight: 3,
          opacity: 0.8,
        }
      },
    }).addTo(map)

    // Fit map to GeoJSON bounds (only on initial load)
    if (!geojsonLayer) {
      const bounds = geojsonLayer.getBounds()
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [1, 1] })
      }
    }
  } catch (e) {
    error.value = `Error adding GeoJSON to map: ${e instanceof Error ? e.message : 'Unknown error'}`
  }
}

// Handle weight changes
const onWeightsChange = () => {
  if (!originalGeoJson.value) return

  // Recalculate scores with new weights
  currentGeoJson.value = recalculateAllScores(originalGeoJson.value, weights)

  // Update map
  addGeoJsonToMap(currentGeoJson.value)
}

// Reset weights to default
const resetWeights = () => {
  weights.maxspeed_int_score = defaultWeights.maxspeed_int_score
  weights.separation_level_score = defaultWeights.separation_level_score
  weights.street_classification_score = defaultWeights.street_classification_score
  weights.lanes_int_score = defaultWeights.lanes_int_score
  onWeightsChange()
}

// Expose methods for parent components
defineExpose({
  recalculateScores: onWeightsChange,
  resetScores: resetWeights,
  setWeights: (newWeights: Partial<ScoreWeights>) => {
    Object.assign(weights, newWeights)
    onWeightsChange()
  },
})
</script>

<style scoped>
.map-component {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
}

.title {
  margin-bottom: 1rem;
}

.map-container {
  flex: 1;
  min-height: 400px;
  border-radius: 4px;
  overflow: hidden;
}

.legend {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background: white;
  padding: 10px 15px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  z-index: 1000;
}

.legend-title {
  font-weight: bold;
  margin-bottom: 8px;
  font-size: 14px;
}

.legend-gradient {
  width: 200px;
  height: 20px;
  background: linear-gradient(
    to right,
    rgb(255, 0, 0) 0%,
    rgb(255, 255, 0) 50%,
    rgb(0, 255, 0) 100%
  );
  border-radius: 2px;
  margin-bottom: 5px;
}

.legend-labels {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #666;
}

.score-controls {
  position: absolute;
  top: 20px;
  left: 20px;
  background: white;
  padding: 15px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  min-width: 250px;
}

.score-control-title {
  font-weight: bold;
  margin-bottom: 12px;
  font-size: 14px;
}

.weight-slider {
  margin-bottom: 12px;
}

.weight-slider label {
  display: block;
  font-size: 13px;
  margin-bottom: 4px;
  color: #333;
}

.weight-slider input[type='range'] {
  width: 100%;
}

.button {
  width: 100%;
  margin-top: 8px;
}
</style>
