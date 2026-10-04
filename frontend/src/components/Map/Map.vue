<script setup lang="ts">
import { AlertCircle, AlertTriangle, Layers, Scale, ShieldCheck } from '@lucide/vue'
import type { BikeInfrastructureModel, ColorMode, GeoJsonData, GeoJsonFeature } from '@/types'
import { colorPalettes, MISSING_DATA_COLOR } from '@/utils/colorScale'
import {
  AttributionControl,
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
import { computed, onMounted, onUnmounted, shallowRef, useTemplateRef, watch } from 'vue'
import { createFeaturePopup } from './tooltipUtils'

setWorkerUrl(workerUrl)

interface Props {
  geojsonData: GeoJsonData | null
  rawGeojsonData?: GeoJsonData | null
  modelConfig: BikeInfrastructureModel
  colorMode?: ColorMode
  error?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  colorMode: 'safety',
  error: null,
})

const emit = defineEmits<{
  ready: []
  'update:colorMode': [mode: ColorMode]
}>()

const mapContainer = useTemplateRef<HTMLElement>('mapContainer')

// MapLibre instances
let map: MapLibreMap | null = null
let currentPopup: Popup | null = null
let selectedFeature: GeoJsonFeature | null = null
const isMapLoaded = shallowRef(false)

const legendColors = computed(() => colorPalettes[props.colorMode])
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
      data: (props.geojsonData as unknown as FeatureCollection) ?? {
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
    selectedFeature = feature
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
          selectedFeature = null
          currentPopup = null
        }
      })
      currentPopup = popup
    }
  })

  // Fit initial bounds if raw or enriched data is already available
  if (props.rawGeojsonData) {
    fitToBounds(props.rawGeojsonData)
  } else if (props.geojsonData) {
    fitToBounds(props.geojsonData)
  }
  emit('ready')
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
  selectedFeature = null
  setSelectedFeature(null)
}

/* ------------------------------------------------------------
  KEYBOARD SHORTCUTS
------------------------------------------------------------ */
const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && currentPopup) {
    if (document.querySelector('.modal.is-active')) return
    clearHighlight()
    currentPopup.remove()
    currentPopup = null
  }
}

/* ------------------------------------------------------------
  MAP INIT
------------------------------------------------------------ */
onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
  if (!mapContainer.value) return
  class CollapsedAttributionControl extends AttributionControl {
    override onAdd(m: MapLibreMap): HTMLElement {
      const el = super.onAdd(m)
      el.classList.remove('maplibregl-compact-show')
      el.removeAttribute('open')
      return el
    }
  }

  map = new MapLibreMap({
    container: mapContainer.value,
    style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
    center: [-71.0995, 42.3876],
    zoom: 14,
    attributionControl: false,
  })
  window._map = map
  map.on('error', (e) => console.error('MapLibre error:', e))

  map.addControl(new NavigationControl({ showCompass: true }), 'top-left')
  map.addControl(
    new CollapsedAttributionControl({
      compact: true,
      customAttribution: '<a href="https://maplibre.org/" target="_blank">MapLibre</a>',
    }),
    'bottom-right',
  )

  map.on('styledata', setupMapLayers)
  map.on('load', setupMapLayers)
  if (map.isStyleLoaded()) {
    setupMapLayers()
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  clearHighlight()
  currentPopup?.remove()
  currentPopup = null
  map?.remove()
  map = null
})

/* ------------------------------------------------------------
  GEOJSON REACTIVITY
------------------------------------------------------------ */
// Watch enriched GeoJSON changes (weights, scores, or palette change)
// Updates layer data and active popup content WITHOUT re-zooming or closing popup
watch(
  () => props.geojsonData,
  (newData) => {
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
    // If a popup is open on a selected street, refresh its score display in-place
    if (currentPopup && selectedFeature) {
      const id = selectedFeature.properties?.__id
      const updatedFeature = typeof id === 'number' ? newData.features[id] : null
      if (updatedFeature) {
        selectedFeature = updatedFeature
        const updatedContent = createFeaturePopup(updatedFeature)
        if (updatedContent) {
          currentPopup.setHTML(updatedContent)
        }
      }
    }
  },
)

// Watch raw GeoJSON changes (ONLY triggers on city switches)
// Resets highlight, closes popup, and fits bounds to the new city
watch(
  () => props.rawGeojsonData,
  (newRaw) => {
    clearHighlight()
    currentPopup?.remove()
    currentPopup = null
    if (newRaw && map && isMapLoaded.value) {
      fitToBounds(newRaw)
    }
  },
)
</script>

<template>
  <div class="box map-component">
    <div
      class="notification is-danger is-light is-flex is-align-items-center map-notification"
      v-if="error"
    >
      <AlertCircle :size="18" class="mr-2" />
      <span>{{ error }}</span>
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
      <div class="legend-sublabels">
        <span>Safer</span>
        <span>Riskier</span>
      </div>

      <!-- Missing data indicator -->
      <div class="legend-missing">
        <div class="legend-missing-block"></div>
        <span class="legend-missing-label">No data</span>
      </div>
    </div>

    <!-- Color Scale Toggle -->
    <div class="color-toggle">
      <div class="color-toggle-label">color scheme</div>
      <div class="segmented-control" role="group" aria-label="color scheme">
        <button
          type="button"
          class="segment-button mode-safety"
          :class="{ active: colorMode === 'safety' }"
          @click="emit('update:colorMode', 'safety')"
          title="Safety (Green to White)"
        >
          <ShieldCheck :size="14" class="mr-1" />
          <span>Safety</span>
        </button>
        <button
          type="button"
          class="segment-button mode-safety-risk"
          :class="{ active: colorMode === 'safety-risk' }"
          @click="emit('update:colorMode', 'safety-risk')"
          title="Safety-Risk (Green to Red)"
        >
          <Scale :size="14" class="mr-1" />
          <span>Safety-Risk</span>
        </button>
        <button
          type="button"
          class="segment-button mode-risk"
          :class="{ active: colorMode === 'risk' }"
          @click="emit('update:colorMode', 'risk')"
          title="Risk (White to Red)"
        >
          <AlertTriangle :size="14" class="mr-1" />
          <span>Risk</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.map-component {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
  padding: 0.5rem;
  --bulma-box-padding: 0.5rem;
}

.map-notification {
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1100;
  margin: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.map-container {
  flex: 1;
  min-height: 400px;
  width: 100%;
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
}

/* Legend */
.legend {
  position: absolute;
  bottom: 18px;
  left: 18px;
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

.legend-sublabels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  font-style: italic;
  color: #666;
  margin-top: 2px;
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
  top: 18px;
  right: 18px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  padding: 6px 8px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.18);
  z-index: 1000;
  transition:
    background-color 0.2s ease,
    box-shadow 0.2s ease;
}

.color-toggle-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #666;
  margin-bottom: 4px;
  padding-left: 2px;
}

.color-toggle:hover {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

.segmented-control {
  display: flex;
  align-items: center;
  gap: 2px;
  background: rgba(0, 0, 0, 0.05);
  padding: 2px;
  border-radius: 6px;
}

.segment-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: #666;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  transition:
    color 0.2s ease,
    background-color 0.2s ease,
    box-shadow 0.2s ease;
  white-space: nowrap;
  user-select: none;
}

.segment-button:hover:not(.active) {
  color: #222;
  background: rgba(255, 255, 255, 0.6);
}

.segment-button.active {
  color: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

.segment-button.mode-safety.active {
  background-color: #2ca25f; /* Green for Safety */
}

.segment-button.mode-safety-risk.active {
  background-color: #d97706; /* Amber for Safety-Risk */
}

.segment-button.mode-risk.active {
  background-color: #b30000; /* Red for Risk */
}

@media (max-width: 600px) {
  .color-toggle {
    top: 14px;
    right: 14px;
    padding: 3px;
  }

  .segment-button {
    padding: 4px 6px;
    font-size: 11px;
  }
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
  color: #222;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

:deep(.maplibregl-popup-anchor-top .maplibregl-popup-tip),
:deep(.maplibregl-popup-anchor-top-left .maplibregl-popup-tip),
:deep(.maplibregl-popup-anchor-top-right .maplibregl-popup-tip) {
  border-bottom-color: rgba(255, 255, 255, 0.92);
}

:deep(.maplibregl-popup-anchor-bottom .maplibregl-popup-tip),
:deep(.maplibregl-popup-anchor-bottom-left .maplibregl-popup-tip),
:deep(.maplibregl-popup-anchor-bottom-right .maplibregl-popup-tip) {
  border-top-color: rgba(255, 255, 255, 0.92);
}

:deep(.maplibregl-popup-anchor-left .maplibregl-popup-tip) {
  border-right-color: rgba(255, 255, 255, 0.92);
}

:deep(.maplibregl-popup-anchor-right .maplibregl-popup-tip) {
  border-left-color: rgba(255, 255, 255, 0.92);
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
