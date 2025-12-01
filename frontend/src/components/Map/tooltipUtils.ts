import type { GeoJsonFeature } from '@/types'
import type L from 'leaflet'

// Import color scale for bar charts
const badColors = ['#fff7ec', '#fee8c8', '#fdbb84', '#e34a33', '#b30000']

/**
 * Get color from badColors gradient based on score
 * @param value - The score value (0-5)
 * @returns Hex color string
 */
const getScoreColor = (value: number): string => {
  const normalized = value / 5 // Normalize to 0-1
  const index = Math.min(Math.floor(normalized * badColors.length), badColors.length - 1)
  return badColors[index] ?? badColors[0] ?? '#fff7ec'
}

/**
 * Creates a small bar chart for score visualization
 * @param value - The score value (0-5)
 * @returns HTML string for the bar chart
 */
const createScoreBar = (value: number): string => {
  const percentage = Math.round((value / 5) * 100)
  const barColor = getScoreColor(value)

  return `
    <div style="background: #f5f5f5; border-radius: 3px; height: 16px; overflow: hidden; position: relative; margin-top: 4px;">
      <div style="background: ${barColor}; height: 100%; width: ${percentage}%; transition: width 0.3s ease;"></div>
      <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; color: #363636;">
        ${value.toFixed(1)}/5
      </div>
    </div>
  `
}

/**
 * Creates a field with optional score bar
 * @param label - The field label
 * @param value - The field value
 * @param scoreValue - Optional score value to display as bar chart
 * @returns HTML string for the field
 */
const createFieldWithScore = (
  label: string,
  value: string | number,
  scoreValue?: number,
): string => {
  const formattedValue = typeof value === 'number' ? value.toFixed(2) : value
  let html = `<div style="margin-bottom: 12px;">
    <div><strong>${label}:</strong> ${formattedValue}</div>`

  if (scoreValue !== undefined) {
    html += createScoreBar(scoreValue)
  }

  html += '</div>'
  return html
}

/**
 * Creates a formatted HTML popup for a GeoJSON feature
 * @param feature - The GeoJSON feature
 * @returns HTML string for the popup
 */
export const createFeaturePopup = (feature: GeoJsonFeature): string => {
  if (!feature.properties) return ''

  const props = feature.properties
  let html = '<div style="min-width: 220px; font-family: sans-serif;">'

  // Name
  if ('name' in props) {
    html += `<div style="margin-bottom: 12px;"><strong>Name:</strong> ${props.name}</div>`
  }

  // Lanes
  if ('lanes_int' in props) {
    html += `<div style="margin-bottom: 12px;"><strong>Lanes:</strong> ${props.lanes_int}</div>`
  }

  // Separation Level with score
  if ('separation_level' in props && props.separation_level !== undefined) {
    html += createFieldWithScore(
      'Separation Level',
      props.separation_level,
      props.separation_level_score,
    )
  }

  // Street Classification with score
  if ('street_classification' in props && props.street_classification !== undefined) {
    html += createFieldWithScore(
      'Street Classification',
      props.street_classification,
      props.street_classification_score,
    )
  }

  // Max Speed with score
  if ('maxspeed_int' in props) {
    const speedDisplay = `${props.maxspeed_int} mph`
    html += createFieldWithScore('Max Speed', speedDisplay, props.maxspeed_int_score)
  }

  // Composite Score with bar chart
  if ('composite_score' in props && props.composite_score !== undefined) {
    html += `<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #dbdbdb;">
      <div><strong>Composite Score:</strong> ${props.composite_score.toFixed(2)}</div>`
    html += createScoreBar(props.composite_score)
    html += '</div>'
  }

  html += '</div>'
  return html
}

/**
 * Binds a popup to a Leaflet layer based on feature properties
 * @param feature - The GeoJSON feature
 * @param layer - The Leaflet layer
 */
export const bindFeaturePopup = (feature: GeoJsonFeature, layer: L.Layer): void => {
  const popupContent = createFeaturePopup(feature)
  if (popupContent && 'bindPopup' in layer) {
    layer.bindPopup(popupContent, { maxWidth: 300 })
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
