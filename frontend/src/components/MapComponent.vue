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

    <!-- Debug Overlay -->
    <div class="debug-overlay">
      <div class="debug-title">Debug Info</div>
      <div class="debug-item">Zoom: {{ currentZoom.toFixed(1) }}</div>
      <div class="debug-item">Line Width: {{ currentLineWidth }}px</div>
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
const currentZoom = ref(15) // Track current zoom level
const currentLineWidth = ref(3) // Track current line width

// GeoJSON data storage
const originalGeoJson = ref<GeoJsonData | null>(null) // Preserve original from server
const currentGeoJson = ref<GeoJsonData | null>(null) // Working copy with recalculated scores
const boundaryGeoJson = ref<any | null>(null) // Somerville boundary

// Score weights (reactive)
const weights = reactive<ScoreWeights>({ ...defaultWeights })

// Leaflet instances
let map: L.Map | null = null
let geojsonLayer: L.GeoJSON | null = null
let boundaryLayer: L.GeoJSON | null = null

// Color palette from light to dark green
const colorPalette = [
  '#ffffe5',
  '#f7fcb9',
  '#d9f0a3',
  '#addd8e',
  '#78c679',
  '#41ab5d',
  '#238443',
  '#006837',
  '#004529',
]

// Color scale function: 0 to 10 using the color palette
const getColorForScore = (score: number): string => {
  // Clamp score between 0 and 10
  const clampedScore = Math.max(0, Math.min(10, score))

  // Normalize to 0-1 range
  const normalized = clampedScore / 10

  // Map to palette index (0 to 8)
  const index = normalized * (colorPalette.length - 1)
  const lowerIndex = Math.floor(index)
  const upperIndex = Math.ceil(index)

  // If exact match, return that color
  if (lowerIndex === upperIndex) {
    return colorPalette[lowerIndex]
  }

  // Otherwise interpolate between two colors
  const ratio = index - lowerIndex
  const lowerColor = colorPalette[lowerIndex]
  const upperColor = colorPalette[upperIndex]

  // Parse hex colors
  const lower = {
    r: parseInt(lowerColor.slice(1, 3), 16),
    g: parseInt(lowerColor.slice(3, 5), 16),
    b: parseInt(lowerColor.slice(5, 7), 16),
  }
  const upper = {
    r: parseInt(upperColor.slice(1, 3), 16),
    g: parseInt(upperColor.slice(3, 5), 16),
    b: parseInt(upperColor.slice(5, 7), 16),
  }

  // Interpolate
  const r = Math.round(lower.r + (upper.r - lower.r) * ratio)
  const g = Math.round(lower.g + (upper.g - lower.g) * ratio)
  const b = Math.round(lower.b + (upper.b - lower.b) * ratio)

  return `rgb(${r}, ${g}, ${b})`
}

// Calculate line weight based on zoom level
const getLineWeight = (zoom: number): number => {
  // Zoom typically ranges from 1-20
  // At zoom 10 or less: thin lines (1-2px)
  // At zoom 15: medium lines (3-4px)
  // At zoom 18+: thick lines (5-7px)
  if (zoom <= 12) {
    return 1
  } else if (zoom <= 14) {
    return 2
  } else if (zoom <= 16) {
    return 3
  } else if (zoom <= 18) {
    return 5
  } else {
    return 7
  }
}

// Initialize map and load GeoJSON
onMounted(async () => {
  if (mapContainer.value) {
    // Initialize map centered on Somerville, MA with more zoom
    map = L.map(mapContainer.value).setView([42.3876, -71.0995], 15)

    var Stadia_StamenTonerLite = L.tileLayer(
      'https://tiles.stadiamaps.com/tiles/stamen_toner_lite/{z}/{x}/{y}{r}.{ext}',
      {
        minZoom: 0,
        maxZoom: 20,
        attribution:
          '&copy; <a href="https://www.stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://www.stamen.com/" target="_blank">Stamen Design</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        ext: 'png',
      },
    )

    Stadia_StamenTonerLite.addTo(map)

    // Add zoom event listener to update line weights dynamically
    map.on('zoomend', () => {
      if (geojsonLayer && map) {
        const zoom = map.getZoom()
        const lineWeight = getLineWeight(zoom)

        // Update debug overlay
        currentZoom.value = zoom
        currentLineWidth.value = lineWeight

        geojsonLayer.setStyle((feature) => {
          const compositeScore = feature?.properties?.composite_score ?? 5
          return {
            color: getColorForScore(compositeScore),
            weight: lineWeight,
            opacity: 0.9,
          }
        })
      }
    })

    // Load the boundary first (so it appears below streets)
    await loadBoundary()

    // Then load the streets GeoJSON
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

// Load boundary GeoJSON
const loadBoundary = async () => {
  try {
    const response = await fetch('/somerville_boundary.geojson')
    if (!response.ok) {
      console.warn('Boundary file not found, skipping...')
      return
    }

    const data = await response.json()
    boundaryGeoJson.value = data

    // Add boundary to map
    addBoundaryToMap(data)
  } catch (e) {
    console.warn('Error loading boundary:', e)
    // Don't set error state - boundary is optional
  }
}

// Add boundary GeoJSON to map
const addBoundaryToMap = (geojsonData: any) => {
  if (!map) return

  try {
    // Remove existing boundary layer if any
    if (boundaryLayer) {
      map.removeLayer(boundaryLayer)
    }

    // Add new boundary layer with light grey, semi-transparent fill
    boundaryLayer = L.geoJSON(geojsonData, {
      style: {
        fillColor: '#cccccc',
        fillOpacity: 0.2,
        color: '#999999',
        weight: 2,
        opacity: 0.5,
      },
    }).addTo(map)
  } catch (e) {
    console.warn('Error adding boundary to map:', e)
  }
}

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

    // Initialize debug overlay values
    if (map) {
      currentZoom.value = map.getZoom()
      currentLineWidth.value = getLineWeight(currentZoom.value)
    }
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

        // Get current zoom level
        const currentZoom = map?.getZoom() ?? 15

        return {
          color: getColorForScore(compositeScore),
          weight: getLineWeight(currentZoom),
          opacity: 0.9,
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
  left: 20px;
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
    #ffffe5 0%,
    #f7fcb9 12.5%,
    #d9f0a3 25%,
    #addd8e 37.5%,
    #78c679 50%,
    #41ab5d 62.5%,
    #238443 75%,
    #006837 87.5%,
    #004529 100%
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

.debug-overlay {
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 10px 15px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  z-index: 1001;
  min-width: 150px;
}

.debug-title {
  font-weight: bold;
  margin-bottom: 6px;
  font-size: 13px;
  color: #00ff00;
}

.debug-item {
  margin-bottom: 3px;
  line-height: 1.4;
}

.score-controls {
  position: absolute;
  top: 80px;
  right: 20px;
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
