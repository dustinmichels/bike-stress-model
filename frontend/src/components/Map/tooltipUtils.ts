import type { GeoJsonFeature } from '@/types'
import type L from 'leaflet'

/**
 * Creates a formatted HTML popup for a GeoJSON feature
 * @param feature - The GeoJSON feature
 * @returns HTML string for the popup
 */
export const createFeaturePopup = (feature: GeoJsonFeature): string => {
  if (!feature.properties) return ''

  return Object.entries(feature.properties)
    .filter(([key]) => !key.startsWith('_')) // Skip internal properties
    .map(([key, value]) => {
      const formattedValue = typeof value === 'number' ? value.toFixed(2) : value
      return `<strong>${key}:</strong> ${formattedValue}`
    })
    .join('<br>')
}

/**
 * Binds a popup to a Leaflet layer based on feature properties
 * @param feature - The GeoJSON feature
 * @param layer - The Leaflet layer
 */
export const bindFeaturePopup = (feature: GeoJsonFeature, layer: L.Layer): void => {
  const popupContent = createFeaturePopup(feature)
  if (popupContent && 'bindPopup' in layer) {
    layer.bindPopup(popupContent)
  }
}

/**
 * Configuration options for feature popups
 */
export interface PopupOptions {
  excludeKeys?: string[]
  includeKeys?: string[]
  formatters?: Record<string, (value: any) => string>
}

/**
 * Creates a customized popup with additional options
 * @param feature - The GeoJSON feature
 * @param options - Popup configuration options
 * @returns HTML string for the popup
 */
export const createCustomPopup = (feature: GeoJsonFeature, options: PopupOptions = {}): string => {
  if (!feature.properties) return ''

  const { excludeKeys = [], includeKeys, formatters = {} } = options

  let entries = Object.entries(feature.properties)

  // Filter by includeKeys if provided
  if (includeKeys) {
    entries = entries.filter(([key]) => includeKeys.includes(key))
  }

  // Exclude specified keys and internal properties
  entries = entries.filter(([key]) => !key.startsWith('_') && !excludeKeys.includes(key))

  return entries
    .map(([key, value]) => {
      // Use custom formatter if available
      const formattedValue = formatters[key]
        ? formatters[key](value)
        : typeof value === 'number'
          ? value.toFixed(2)
          : value

      return `<strong>${key}:</strong> ${formattedValue}`
    })
    .join('<br>')
}
