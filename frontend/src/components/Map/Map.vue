<template>
  <div class="box map-component">
    <div class="notification is-danger is-light is-flex is-align-items-center" v-if="error">
      <AlertCircle :size="18" class="mr-2" />
      <span>{{ error }}</span>
    </div>

    <div class="notification is-info is-light is-flex is-align-items-center" v-if="loading">
      <Loader2 :size="18" class="mr-2 spin-icon" />
      <span>Loading map data...</span>
    </div>

    <div ref="mapContainer" class="map-container"></div>

    <!-- Legend -->
    <div class="legend">
      <div class="legend-title is-flex is-align-items-center">
        <Layers :size="14" class="mr-1" />
        <span>Composite Score</span>
      </div>

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

    <!-- Color Scale Toggle -->
    <div class="color-toggle">
      <div class="toggle-container">
        <span
          class="toggle-label is-inline-flex is-align-items-center"
          :class="{ active: useGoodColors }"
        >
          <ShieldCheck :size="14" class="mr-1" />
          <span>Safety</span>
        </span>
        <label class="switch">
          <input type="checkbox" :checked="!useGoodColors" @change="$emit('toggleColors')" />
          <span class="slider"></span>
        </label>
        <span
          class="toggle-label is-inline-flex is-align-items-center"
          :class="{ active: !useGoodColors }"
        >
          <AlertTriangle :size="14" class="mr-1" />
          <span>Risk</span>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { AlertCircle, AlertTriangle, Layers, Loader2, ShieldCheck } from '@lucide/vue'
import type { BikeInfrastructureModel, GeoJsonData, GeoJsonFeature } from '@/types'
import { badColors, goodColors } from '@/utils/colorScale'
import { calculateAllScores } from '@/utils/scoreCalculator'
import {
  LngLatBounds,
  Map as MapLibreMap,
  NavigationControl,
  Popup,
  setWorkerUrl,
  type FilterSpecification,
  type GeoJSONSource,
  type MapLayerMouseEvent,
} from 'maplibre-gl'
import type { FeatureCollection } from 'geojson'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { createFeaturePopup } from './tooltipUtils'

setWorkerUrl(workerUrl)
// Props
interface Props {
  geojsonData: GeoJsonData | null
  modelConfig: BikeInfrastructureModel
  useGoodColors?: boolean
}
const props = withDefaults(defineProps<Props>(), {
  useGoodColors: true,
})

// Extract weights from modelConfig
const modelWeights = computed(() => ({
  separation_level: props.modelConfig.separation_level.weight,
  speed: props.modelConfig.speed_limit.weight,
  busyness: props.modelConfig.street_classification.weight,
}))

// Emits
const emit = defineEmits<{
  toggleColors: []
}>()

// Refs
const mapContainer = ref<HTMLElement | null>(null)
const error = ref('')
const loading = ref(false)

// MapLibre instances
let map: MapLibreMap | null = null
let currentPopup: Popup | null = null
const isMapLoaded = ref(false)
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
    const scores = calculateAllScores(feature.properties, props.modelConfig, modelWeights.value)

    // Add newly computed scores to properties
    Object.assign(feature.properties, scores)
    feature.properties.color = getColorForScore(scores.composite_score)
    feature.id = index
    feature.properties.__id = index
    scoresSummary.push(scores.composite_score)
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
  BOUNDS CALCULATION
------------------------------------------------------------ */
const fitToBounds = (data: GeoJsonData) => {
  if (!map) return
  const bounds = new LngLatBounds()
  let hasCoords = false

  const processCoords = (coords: unknown) => {
    if (
      Array.isArray(coords) &&
      coords.length >= 2 &&
      typeof coords[0] === 'number' &&
      typeof coords[1] === 'number'
    ) {
      bounds.extend([coords[0], coords[1]])
      hasCoords = true
    } else if (Array.isArray(coords)) {
      for (const item of coords) {
        processCoords(item)
      }
    }
  }

  for (const feature of data.features) {
    if (feature.geometry?.coordinates) {
      processCoords(feature.geometry.coordinates)
    }
  }

  if (hasCoords) {
    map.fitBounds(bounds, { padding: 50, maxZoom: 16 })
  }
}
/* ------------------------------------------------------------
  SETUP LAYERS
------------------------------------------------------------ */
const setupMapLayers = () => {
  if (!map || isMapLoaded.value) return
  if (!map.isStyleLoaded()) return
  isMapLoaded.value = true

  // Add GeoJSON source
  if (!map.getSource('streets-data')) {
    map.addSource('streets-data', {
      type: 'geojson',
      data: (computedGeoJson.value as unknown as FeatureCollection) ?? {
        type: 'FeatureCollection',
        features: [],
      },
    })
  }

  // Add main styled line layer
  if (!map.getLayer('streets-line')) {
    map.addLayer({
      id: 'streets-line',
      type: 'line',
      source: 'streets-data',
      layout: {
        'line-join': 'round',
        'line-cap': 'round',
      },
      paint: {
        'line-color': ['coalesce', ['get', 'color'], MISSING_DATA_COLOR],
        'line-width': [
          'interpolate',
          ['linear'],
          ['zoom'],
          10,
          1,
          12,
          1.5,
          14,
          2.5,
          16,
          4,
          18,
          6,
          20,
          8,
        ],
        'line-opacity': 0.9,
      },
    })
  }

  // Add highlight layers for selected street using existing streets-data source
  if (!map.getLayer('selected-street-casing')) {
    map.addLayer({
      id: 'selected-street-casing',
      type: 'line',
      source: 'streets-data',
      filter: ['==', ['get', '__id'], -1],
      layout: {
        'line-join': 'round',
        'line-cap': 'round',
      },
      paint: {
        'line-color': '#ffffff',
        'line-width': [
          'interpolate',
          ['linear'],
          ['zoom'],
          10,
          4,
          12,
          5.5,
          14,
          7.5,
          16,
          10,
          18,
          13,
          20,
          16,
        ],
        'line-opacity': 0.9,
      },
    })
  }

  if (!map.getLayer('selected-street-line')) {
    map.addLayer({
      id: 'selected-street-line',
      type: 'line',
      source: 'streets-data',
      filter: ['==', ['get', '__id'], -1],
      layout: {
        'line-join': 'round',
        'line-cap': 'round',
      },
      paint: {
        'line-color': '#00e5ff',
        'line-width': [
          'interpolate',
          ['linear'],
          ['zoom'],
          10,
          2.5,
          12,
          3.5,
          14,
          5,
          16,
          7,
          18,
          9.5,
          20,
          12,
        ],
        'line-opacity': 1,
      },
    })
  }

  // Hover interaction using 10px bounding box
  map.on('mousemove', (e: MapLayerMouseEvent) => {
    if (!map) return
    const bbox: [[number, number], [number, number]] = [
      [e.point.x - 5, e.point.y - 5],
      [e.point.x + 5, e.point.y + 5],
    ]
    const features = map.queryRenderedFeatures(bbox, {
      layers: ['streets-line', 'selected-street-line'],
    })
    map.getCanvas().style.cursor = features.length > 0 ? 'pointer' : ''
  })

  // Click handler for popup and segment highlight using 10px bounding box
  map.on('click', (e: MapLayerMouseEvent) => {
    if (!map) return
    const bbox: [[number, number], [number, number]] = [
      [e.point.x - 5, e.point.y - 5],
      [e.point.x + 5, e.point.y + 5],
    ]
    const features = map.queryRenderedFeatures(bbox, {
      layers: ['streets-line', 'selected-street-line'],
    })
    if (features.length === 0) {
      clearHighlight()
      if (currentPopup) {
        currentPopup.remove()
        currentPopup = null
      }
      return
    }

    const feature = features[0] as unknown as GeoJsonFeature
    setSelectedFeature(feature)

    const popupContent = createFeaturePopup(feature)
    if (popupContent) {
      if (currentPopup) {
        const oldPopup = currentPopup
        currentPopup = null
        oldPopup.remove()
      }
      const popup = new Popup({ maxWidth: '320px' })
        .setLngLat(e.lngLat)
        .setHTML(popupContent)
        .addTo(map)

      popup.on('close', () => {
        if (currentPopup === popup) {
          clearHighlight()
          currentPopup = null
        }
      })
      currentPopup = popup
    }
  })

  // Fit initial bounds if data is already available
  if (props.geojsonData) {
    fitToBounds(props.geojsonData)
  }
}

const setSelectedFeature = (feature: GeoJsonFeature | null) => {
  if (!map) return
  if (!map.getLayer('selected-street-line') || !map.getLayer('selected-street-casing')) return

  if (!feature) {
    const emptyFilter: FilterSpecification = ['==', ['get', '__id'], -1]
    map.setFilter('selected-street-casing', emptyFilter)
    map.setFilter('selected-street-line', emptyFilter)
    return
  }

  const id = feature.properties?.__id
  let filter: FilterSpecification
  if (typeof id === 'number' || typeof id === 'string') {
    filter = ['==', ['get', '__id'], id]
  } else if (
    typeof feature.properties?.u === 'number' &&
    typeof feature.properties?.v === 'number'
  ) {
    const key = typeof feature.properties.key === 'number' ? feature.properties.key : 0
    filter = [
      'all',
      ['==', ['get', 'u'], feature.properties.u],
      ['==', ['get', 'v'], feature.properties.v],
      ['==', ['get', 'key'], key],
    ]
  } else {
    filter = ['==', ['get', 'name'], feature.properties?.name ?? '']
  }

  map.setFilter('selected-street-casing', filter)
  map.setFilter('selected-street-line', filter)
}

const clearHighlight = () => {
  setSelectedFeature(null)
}
/* ------------------------------------------------------------
  MAP INIT
------------------------------------------------------------ */
onMounted(() => {
  if (!mapContainer.value) return

  map = new MapLibreMap({
    container: mapContainer.value,
    style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
    center: [-71.0995, 42.3876],
    zoom: 14,
  })
  window._map = map
  map.on('error', (e) => console.error('MapLibre error:', e))

  map.addControl(new NavigationControl({ showCompass: true }), 'top-left')

  map.on('styledata', setupMapLayers)
  map.on('load', setupMapLayers)
  if (map.isStyleLoaded()) {
    setupMapLayers()
  }
})

onUnmounted(() => {
  clearHighlight()
  currentPopup?.remove()
  currentPopup = null
  map?.remove()
  map = null
})

/* ------------------------------------------------------------
  GEOJSON REACTIVITY
------------------------------------------------------------ */
// Watch computed GeoJSON to update map layer data
watch(computedGeoJson, (newData) => {
  if (!map || !newData) return
  if (!isMapLoaded.value) {
    if (map.isStyleLoaded()) {
      setupMapLayers()
    }
    return
  }
  const source = map.getSource('streets-data') as GeoJSONSource | undefined
  if (source) {
    source.setData(newData as unknown as FeatureCollection)
  }
})
// Watch raw geojsonData changes (e.g. city change) to fit bounds
watch(
  () => props.geojsonData,
  (newData) => {
    clearHighlight()
    currentPopup?.remove()
    currentPopup = null
    if (newData && map && isMapLoaded.value) {
      fitToBounds(newData)
    }
  },
)
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

/* Color toggle */
.color-toggle {
  position: absolute;
  top: 32px;
  right: 32px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  padding: 10px 15px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.18);
  z-index: 1000;
  transition:
    background-color 0.2s ease,
    box-shadow 0.2s ease;
}

.color-toggle:hover {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
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

/* MapLibre popup styles */
:deep(.maplibregl-popup) {
  max-width: 320px;
  font-family:
    BlinkMacSystemFont,
    -apple-system,
    'Segoe UI',
    Roboto,
    Oxygen,
    Ubuntu,
    Cantarell,
    'Fira Sans',
    'Droid Sans',
    'Helvetica Neue',
    Helvetica,
    Arial,
    sans-serif;
}

:deep(.maplibregl-popup-content) {
  padding: 12px 14px;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.28);
  color: #363636;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

:deep(.maplibregl-popup-anchor-top .maplibregl-popup-tip),
:deep(.maplibregl-popup-anchor-top-left .maplibregl-popup-tip),
:deep(.maplibregl-popup-anchor-top-right .maplibregl-popup-tip) {
  border-bottom-color: rgba(255, 255, 255, 0.85);
}

:deep(.maplibregl-popup-anchor-bottom .maplibregl-popup-tip),
:deep(.maplibregl-popup-anchor-bottom-left .maplibregl-popup-tip),
:deep(.maplibregl-popup-anchor-bottom-right .maplibregl-popup-tip) {
  border-top-color: rgba(255, 255, 255, 0.85);
}

:deep(.maplibregl-popup-anchor-left .maplibregl-popup-tip) {
  border-right-color: rgba(255, 255, 255, 0.85);
}

:deep(.maplibregl-popup-anchor-right .maplibregl-popup-tip) {
  border-left-color: rgba(255, 255, 255, 0.85);
}

:deep(.maplibregl-popup-close-button) {
  padding: 4px 8px;
  font-size: 16px;
  color: #888;
}

:deep(.maplibregl-popup-close-button:hover) {
  color: #222;
  background: transparent;
}

:deep(.maplibregl-ctrl-group) {
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
</style>
