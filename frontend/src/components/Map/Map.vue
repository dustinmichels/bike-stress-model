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

      <div class="legend-colors">
        <div
          v-for="(color, index) in legendColors"
          :key="index"
          :style="{ backgroundColor: color }"
          class="legend-color-block"
        ></div>
      </div>

      <div class="legend-labels">
        <span v-for="n in legendColors.length" :key="n - 1">{{ n - 1 }}</span>
      </div>

      <!-- Missing data indicator -->
      <div class="legend-missing">
        <div class="legend-missing-block"></div>
        <span class="legend-missing-label">No data</span>
      </div>
    </div>

    <!-- Boundary Toggle -->
    <div class="boundary-toggle">
      <label class="checkbox">
        <input type="checkbox" v-model="showBoundary" @change="toggleBoundary" />
        Show Boundary
      </label>
    </div>

    <!-- Color Scale Toggle -->
    <div class="color-toggle">
      <div class="toggle-container">
        <span class="toggle-label" :class="{ active: useGoodColors }">Safety</span>
        <label class="switch">
          <input type="checkbox" :checked="!useGoodColors" @change="$emit('toggleColors')" />
          <span class="slider"></span>
        </label>
        <span class="toggle-label" :class="{ active: !useGoodColors }">Risk</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { BikeInfrastructureModel, GeoJsonData, GeoJsonFeature, ModelWeights } from '@/types'
import { badColors, goodColors } from '@/utils/colorScale'
import { calculateAllScores } from '@/utils/scoreCalculator'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { bindFeaturePopup } from './tooltipUtils'

// Fix Leaflet marker assets
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
  geojsonData: GeoJsonData | null
  modelConfig: BikeInfrastructureModel
  modelWeights: ModelWeights
  useGoodColors?: boolean
}
const props = withDefaults(defineProps<Props>(), {
  useGoodColors: true,
})

// Emits
const emit = defineEmits<{
  toggleColors: []
}>()

// Refs
const mapContainer = ref<HTMLElement | null>(null)
const error = ref('')
const loading = ref(false)
const showBoundary = ref(true)

// Boundary data
const boundaryGeoJson = ref<any | null>(null)

// Leaflet layers
let map: L.Map | null = null
let geojsonLayer: L.GeoJSON | null = null
let boundaryLayer: L.GeoJSON | null = null

/* ------------------------------------------------------------
  COLOR SCALE
------------------------------------------------------------ */

const MISSING_DATA_COLOR = '#808080' // Grey for missing data

const legendColors = computed(() => (props.useGoodColors ? goodColors : badColors))

const getColorForScore = (score: number | null): string => {
  // Return grey if score is null (missing data)
  if (score === null || score === undefined) {
    return MISSING_DATA_COLOR
  }

  const colors = props.useGoodColors ? goodColors : badColors
  const clamped = Math.max(0, Math.min(5, score))
  const idx = Math.round((clamped / 5) * (colors.length - 1))
  return colors[idx] ?? colors[0] ?? MISSING_DATA_COLOR
}

/* ------------------------------------------------------------
  COMPUTE SCORES FOR GEOJSON
------------------------------------------------------------ */

const computedGeoJson = computed<GeoJsonData | null>(() => {
  if (!props.geojsonData) return null

  // Deep copy the GeoJSON
  const data = JSON.parse(JSON.stringify(props.geojsonData))

  const scoresSummary: (number | null)[] = []
  let missingDataCount = 0

  // Calculate scores for each feature
  data.features.forEach((feature: GeoJsonFeature, index: number) => {
    // IMPORTANT: Remove any pre-existing score columns from the GeoJSON
    // We want to use ONLY our newly calculated scores
    delete feature.properties.separation_level_score
    delete feature.properties.street_classification_score
    delete feature.properties.maxspeed_int_score
    delete feature.properties.composite_score

    // Calculate fresh scores
    const scores = calculateAllScores(feature.properties, props.modelConfig, props.modelWeights)

    // Add newly computed scores to properties
    Object.assign(feature.properties, scores)
    scoresSummary.push(scores.composite_score)

    // Count missing data
    if (scores.composite_score === null) {
      missingDataCount++
    }

    // Log first 5 features for debugging
    if (index < 5) {
      console.log(`Feature ${index}:`, {
        name: feature.properties.name,
        separation_level: feature.properties.separation_level,
        street_classification: feature.properties.street_classification,
        maxspeed_int: feature.properties.maxspeed_int,
        calculated_scores: scores,
      })
    }
  })

  // Filter out null scores for statistics
  const validScores = scoresSummary.filter((s): s is number => s !== null)

  // Log score distribution
  const uniqueScores = new Set(validScores)
  console.log('Score calculation summary:', {
    totalFeatures: data.features.length,
    missingDataFeatures: missingDataCount,
    featuresWithData: validScores.length,
    uniqueScores: uniqueScores.size,
    scoreRange:
      validScores.length > 0
        ? {
            min: Math.min(...validScores),
            max: Math.max(...validScores),
            avg: (validScores.reduce((a, b) => a + b, 0) / validScores.length).toFixed(2),
          }
        : 'No valid scores',
    sampleScores: scoresSummary.slice(0, 10),
  })

  if (uniqueScores.size === 1 && validScores.length > 0) {
    console.warn('⚠️ ALL STREETS WITH DATA HAVE THE SAME SCORE:', validScores[0])
    console.warn('This means the scoring logic is not varying. Check the logs above.')
  }

  if (missingDataCount > 0) {
    console.log(`ℹ️ ${missingDataCount} streets have missing data and will be colored grey`)
  }

  return data
})

/* ------------------------------------------------------------
  LINE WIDTH VS ZOOM
------------------------------------------------------------ */
const getLineWeight = (zoom: number): number => {
  if (zoom <= 12) return 1
  if (zoom <= 14) return 2
  if (zoom <= 16) return 3
  if (zoom <= 18) return 5
  return 7
}

/* ------------------------------------------------------------
  MAP INIT
------------------------------------------------------------ */
onMounted(async () => {
  if (mapContainer.value) {
    map = L.map(mapContainer.value).setView([42.3876, -71.0995], 15)

    L.tileLayer('https://tiles.stadiamaps.com/tiles/stamen_toner_dark/{z}/{x}/{y}{r}.png', {
      minZoom: 0,
      maxZoom: 20,
      attribution:
        '&copy; <a href="https://www.stadiamaps.com/">Stadia Maps</a> ' +
        '&copy; <a href="https://www.stamen.com/">Stamen Design</a> ' +
        '&copy; <a href="https://openmaptiles.org/">OpenMapTiles</a> ' +
        '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>',
    }).addTo(map)

    map.on('zoomend', () => {
      if (geojsonLayer && map) {
        const zoom = map.getZoom()
        const lineWeight = getLineWeight(zoom)

        geojsonLayer.setStyle((feature) => {
          const score = feature?.properties?.composite_score ?? null
          return {
            color: getColorForScore(score),
            weight: lineWeight,
            opacity: 0.9,
          }
        })
      }
    })

    await loadBoundary()
  }
})

onUnmounted(() => {
  map?.remove()
  map = null
})

/* ------------------------------------------------------------
  BOUNDARY
------------------------------------------------------------ */
const loadBoundary = async () => {
  try {
    const response = await fetch('/somerville_boundary.geojson')
    if (!response.ok) return

    const data = await response.json()
    boundaryGeoJson.value = data
    addBoundaryToMap(data)
  } catch {}
}

const addBoundaryToMap = (geojsonData: any) => {
  if (!map) return

  if (boundaryLayer) map.removeLayer(boundaryLayer)

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
}

/* ------------------------------------------------------------
  GEOJSON RENDERING
------------------------------------------------------------ */
const addGeoJsonToMap = (geojsonData: GeoJsonData) => {
  if (!map) return

  if (geojsonLayer) map.removeLayer(geojsonLayer)

  geojsonLayer = L.geoJSON(geojsonData as any, {
    onEachFeature: (feature, layer) => {
      bindFeaturePopup(feature, layer)
    },
    style: (feature) => {
      const score = feature?.properties?.composite_score ?? null
      const zoom = map?.getZoom() ?? 15

      return {
        color: getColorForScore(score),
        weight: getLineWeight(zoom),
        opacity: 0.9,
      }
    },
  }).addTo(map)

  const bounds = geojsonLayer.getBounds()
  if (bounds.isValid()) map.fitBounds(bounds, { padding: [50, 50] })
}

// Watch for changes to computed GeoJSON and re-render
watch(
  computedGeoJson,
  (newData) => {
    if (newData) {
      addGeoJsonToMap(newData)
    }
  },
  { immediate: true },
)

// Watch for color scheme changes
watch(
  () => props.useGoodColors,
  () => {
    if (geojsonLayer) {
      geojsonLayer.setStyle((feature) => {
        const score = feature?.properties?.composite_score ?? null
        const zoom = map?.getZoom() ?? 15
        return {
          color: getColorForScore(score),
          weight: getLineWeight(zoom),
          opacity: 0.9,
        }
      })
    }
  },
)

/* ------------------------------------------------------------
  BOUNDARY TOGGLE
------------------------------------------------------------ */
const toggleBoundary = () => {
  if (!map || !boundaryLayer) return
  showBoundary.value ? map.addLayer(boundaryLayer) : map.removeLayer(boundaryLayer)
}
</script>

<style scoped>
.map-component {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
}

.map-container {
  flex: 1;
  min-height: 400px;
  border-radius: 4px;
  overflow: hidden;
}

/* Legend */
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

.legend-colors {
  display: flex;
  gap: 2px;
  margin-bottom: 5px;
}

.legend-color-block {
  flex: 1;
  height: 20px;
  border-radius: 2px;
  border: 1px solid #ccc;
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

.legend-missing {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid #e0e0e0;
}

.legend-missing-block {
  width: 30px;
  height: 20px;
  background-color: #808080;
  border-radius: 2px;
  border: 1px solid #ccc;
}

.legend-missing-label {
  font-size: 11px;
  color: #666;
}

/* Boundary toggle */
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
  gap: 8px;
  align-items: center;
}

/* Color toggle */
.color-toggle {
  position: absolute;
  bottom: 80px;
  right: 20px;
  background: white;
  padding: 10px 15px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  z-index: 1000;
}

.toggle-container {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toggle-label {
  font-size: 13px;
  font-weight: 500;
  color: #999;
  transition: color 0.3s ease;
}

.toggle-label.active {
  color: #333;
  font-weight: 600;
}

/* iOS-style toggle switch */
.switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #48c774;
  transition: 0.3s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: '';
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #f14668;
}

input:checked + .slider:before {
  transform: translateX(24px);
}

input:focus + .slider {
  box-shadow: 0 0 1px #48c774;
}

input:checked:focus + .slider {
  box-shadow: 0 0 1px #f14668;
}
</style>
