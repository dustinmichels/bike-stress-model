<template>
  <div class="box map-component">
    <div class="notification is-danger is-light" v-if="error">
      {{ error }}
    </div>

    <div class="notification is-info is-light" v-if="loading">Loading map data...</div>

    <div ref="mapContainer" class="map-container"></div>
  </div>
</template>

<script setup lang="ts">
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { onMounted, onUnmounted, ref } from 'vue'

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

// Refs
const mapContainer = ref<HTMLElement | null>(null)
const error = ref('')
const loading = ref(true)

let map: L.Map | null = null
let geojsonLayer: L.GeoJSON | null = null

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
    addGeoJsonToMap(data)
  } catch (e) {
    error.value = `Error loading GeoJSON: ${e instanceof Error ? e.message : 'Unknown error'}`
  } finally {
    loading.value = false
  }
}

// Add GeoJSON to map
const addGeoJsonToMap = (geojsonData: any) => {
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
            .map(([key, value]) => `<strong>${key}:</strong> ${value}`)
            .join('<br>')
          layer.bindPopup(popupContent)
        }
      },
      style: (feature) => {
        // Style for streets with thicker lines
        return {
          color: '#3273dc',
          weight: 2,
          opacity: 0.8,
        }
      },
    }).addTo(map)

    // Fit map to GeoJSON bounds
    const bounds = geojsonLayer.getBounds()
    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [1, 1] })
    }
  } catch (e) {
    error.value = `Error adding GeoJSON to map: ${e instanceof Error ? e.message : 'Unknown error'}`
  }
}
</script>

<style scoped>
.map-component {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
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
</style>
