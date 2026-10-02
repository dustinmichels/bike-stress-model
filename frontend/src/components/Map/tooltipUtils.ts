import type { GeoJsonFeature } from '@/types'
import { icons } from 'lucide'
import { Popup, type LngLatLike, type Map as MapLibreMap } from 'maplibre-gl'

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
const renderLucideSvg = (
  iconDef: (typeof icons)[keyof typeof icons],
  size = 14,
  color = 'currentColor',
): string => {
  const children = iconDef
    .map(([tag, attrs]) => {
      const attrStr = Object.entries(attrs)
        .map(([k, v]) => `${k}="${v}"`)
        .join(' ')
      return `<${tag} ${attrStr}></${tag}>`
    })
    .join('')
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -2px; margin-right: 5px; display: inline-block;">${children}</svg>`
}

/**
 * Creates a small bar chart for score visualization
 * @param value - The score value (0-5), or null if no data
 * @returns HTML string for the bar chart or "No data" message
 */
const createScoreBar = (value: number | string | null | undefined): string => {
  // Handle null/undefined values
  if (value === null || value === undefined || value === '') {
    return `
      <div style="background: rgba(0, 0, 0, 0.06); border-radius: 3px; height: 16px; overflow: hidden; position: relative; margin-top: 4px;">
        <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; font-size: 10px; font-style: italic; color: #999;">
          No data
        </div>
      </div>
    `
  }

  const num = typeof value === 'number' ? value : parseFloat(value)
  if (isNaN(num)) {
    return `
      <div style="background: rgba(0, 0, 0, 0.06); border-radius: 3px; height: 16px; overflow: hidden; position: relative; margin-top: 4px;">
        <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; font-size: 10px; font-style: italic; color: #999;">
          No data
        </div>
      </div>
    `
  }

  const clamped = Math.max(0, Math.min(5, num))
  const percentage = Math.round((clamped / 5) * 100)
  const barColor = getScoreColor(clamped)

  return `
    <div style="background: rgba(0, 0, 0, 0.06); border-radius: 3px; height: 16px; overflow: hidden; position: relative; margin-top: 4px;">
      <div style="background: ${barColor}; height: 100%; width: ${percentage}%; transition: width 0.3s ease;"></div>
      <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; color: #363636;">
        ${num.toFixed(1)}/5
      </div>
    </div>
  `
}

/**
 * Creates a field with optional score bar
 * @param label - The field label
 * @param value - The field value
 * @param scoreValue - Optional score value to display as bar chart (can be null)
 * @returns HTML string for the field
 */
const createFieldWithScore = (
  label: string,
  value: string | number,
  scoreValue?: number | string | null,
  iconSvg?: string,
): string => {
  const formattedValue = typeof value === 'number' ? value.toFixed(2) : value
  let html = `<div style="margin-bottom: 12px;">
    <div style="display: flex; align-items: center; margin-bottom: 2px;">${iconSvg ?? ''}<strong>${label}:</strong>&nbsp;<span>${formattedValue}</span></div>`

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
    html += `<div style="margin-bottom: 12px; display: flex; align-items: center;">${renderLucideSvg(icons.MapPin, 14, '#4a4a4a')}<strong>Name:</strong>&nbsp;<span>${props.name}</span></div>`
  }

  // Lanes
  if ('lanes_int' in props) {
    html += `<div style="margin-bottom: 12px;"><strong>Lanes:</strong>&nbsp;<span>${props.lanes_int}</span></div>`
  }

  // Separation Level with score
  if ('separation_level' in props && props.separation_level !== undefined) {
    html += createFieldWithScore(
      'Separation Level',
      props.separation_level,
      props.separation_level_score,
      renderLucideSvg(icons.Shield, 14, '#3273dc'),
    )
  }

  // Street Classification with score
  if ('street_classification' in props && props.street_classification !== undefined) {
    html += createFieldWithScore(
      'Street Classification',
      props.street_classification,
      props.street_classification_score,
      renderLucideSvg(icons.Car, 14, '#e67e22'),
    )
  }

  // Max Speed with score
  if ('maxspeed_int' in props) {
    const speedDisplay = `${props.maxspeed_int} mph`
    html += createFieldWithScore(
      'Max Speed',
      speedDisplay,
      props.maxspeed_int_score,
      renderLucideSvg(icons.Gauge, 14, '#48c774'),
    )
  }

  // Composite Score with bar chart
  if ('composite_score' in props) {
    const rawScore = props.composite_score
    const numScore =
      typeof rawScore === 'number'
        ? rawScore
        : rawScore !== null && rawScore !== undefined
          ? parseFloat(String(rawScore))
          : null

    const compositeIcon = renderLucideSvg(icons.Layers, 14, '#363636')
    if (numScore !== null && !isNaN(numScore)) {
      html += `<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(0, 0, 0, 0.1);">
        <div style="display: flex; align-items: center; margin-bottom: 2px;">${compositeIcon}<strong>Composite Score:</strong>&nbsp;<span>${numScore.toFixed(2)}</span></div>`
      html += createScoreBar(numScore)
      html += '</div>'
    } else {
      // Show "No data" for composite score
      html += `<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(0, 0, 0, 0.1);">
        <div style="display: flex; align-items: center; margin-bottom: 2px;">${compositeIcon}<strong>Composite Score:</strong>&nbsp;<span style="font-style: italic; color: #999;">No data</span></div>`
      html += createScoreBar(null)
      html += '</div>'
    }
  }

  html += '</div>'
  return html
}

/**
 * Displays a popup on a MapLibre map based on feature properties
 * @param map - The MapLibre Map instance
 * @param feature - The GeoJSON feature
 * @param lngLat - Coordinates where the popup should appear
 */
export const showFeaturePopup = (
  map: MapLibreMap,
  feature: GeoJsonFeature,
  lngLat: LngLatLike,
): Popup | null => {
  const popupContent = createFeaturePopup(feature)
  if (!popupContent) return null
  return new Popup({ maxWidth: '320px' }).setLngLat(lngLat).setHTML(popupContent).addTo(map)
}

/**
 * Configuration options for feature popups
 */
export interface PopupOptions {
  excludeKeys?: string[]
  includeKeys?: string[]
  formatters?: Record<string, (value: unknown) => string>
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
      // Handle null values
      if (value === null || value === undefined) {
        return `<strong>${key}:</strong> <span style="font-style: italic; color: #999;">No data</span>`
      }

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
