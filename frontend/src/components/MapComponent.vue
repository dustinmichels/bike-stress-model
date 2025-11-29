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
        <span>0</span>
        <span>1</span>
        <span>2</span>
        <span>3</span>
        <span>4</span>
        <span>5</span>
        <span>6</span>
        <span>7</span>
        <span>8</span>
        <span>9</span>
        <span>10</span>
      </div>
    </div>

    <!-- Boundary Toggle -->
    <div class="boundary-toggle">
      <label class="checkbox">
        <input type="checkbox" v-model="showBoundary" @change="toggleBoundary" />
        Show Boundary
      </label>
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
const showBoundary = ref(true) // Track boundary visibility

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

// Color palette: 11 distinct colors for scores 0-10
const colorPalette = [
  '#ffffe5', // 0
  '#f7fcb9', // 1
  '#d9f0a3', // 2
  '#addd8e', // 3
  '#78c679', // 4
  '#41ab5d', // 5
  '#238443', // 6
  '#006837', // 7
  '#005a32', // 8
  '#004529', // 9
  '#003320', // 10
]

// Color scale function: 0 to 10 using the 11 discrete colors
const getColorForScore = (score: number): string => {
  // Clamp score between 0 and 10
  const clampedScore = Math.max(0, Math.min(10, score))

  // Round to nearest integer to get discrete color index
  const index = Math.round(clampedScore)

  return colorPalette[index]
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

    var Stadia_StamenTonerDark = L.tileLayer(
      'https://tiles.stadiamaps.com/tiles/stamen_toner_dark/{z}/{x}/{y}{r}.{ext}',
      {
        minZoom: 0,
        maxZoom: 20,
        attribution:
          '&copy; <a href="https://www.stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://www.stamen.com/" target="_blank">Stamen Design</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        ext: 'png',
      },
    )

    var CartoDB_DarkMatter = L.tileLayer(
      'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
      {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20,
      },
    )

    // Stadia_StamenTonerLite.addTo(map)
    // CartoDB_DarkMatter.addTo(map)
    Stadia_StamenTonerDark.addTo(map)

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

    // Add new boundary layer with fun pink color and subtle fill
    boundaryLayer = L.geoJSON(geojsonData, {
      style: {
        fillColor: '#001a33',
        fillOpacity: 0.08,
        color: '#ff1493',
        weight: 4,
        opacity: 0.7,
        dashArray: '4 6',
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

    // Fit map to GeoJSON bounds
    const bounds = geojsonLayer.getBounds()
    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [50, 50] })
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

// Toggle boundary visibility
const toggleBoundary = () => {
  if (!map || !boundaryLayer) return

  if (showBoundary.value) {
    map.addLayer(boundaryLayer)
  } else {
    map.removeLayer(boundaryLayer)
  }
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
  width: 220px;
  height: 20px;
  background: linear-gradient(
    to right,
    #ffffe5 0%,
    #ffffe5 9.09%,
    #f7fcb9 9.09%,
    #f7fcb9 18.18%,
    #d9f0a3 18.18%,
    #d9f0a3 27.27%,
    #addd8e 27.27%,
    #addd8e 36.36%,
    #78c679 36.36%,
    #78c679 45.45%,
    #41ab5d 45.45%,
    #41ab5d 54.54%,
    #238443 54.54%,
    #238443 63.63%,
    #006837 63.63%,
    #006837 72.72%,
    #005a32 72.72%,
    #005a32 81.81%,
    #004529 81.81%,
    #004529 90.9%,
    #003320 90.9%,
    #003320 100%
  );
  border-radius: 2px;
  margin-bottom: 5px;
}

.legend-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: #666;
}

.legend-labels span {
  width: 20px;
  text-align: center;
}

.boundary-toggle {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background: white;
  padding: 10px 15px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  z-index: 1000;
}

.boundary-toggle .checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  cursor: pointer;
  margin: 0;
}

.boundary-toggle input[type='checkbox'] {
  cursor: pointer;
  width: 16px;
  height: 16px;
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
