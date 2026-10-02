import type { GeoJsonFeature } from '@/types'
import { Car, Gauge, Layers, MapPin, Shield, type IconNode } from 'lucide'
import { badColors, MAX_SCORE, scoreToColor } from '@/utils/colorScale'

export const escapeHtml = (value: unknown): string => {
  if (value === null || value === undefined) return ''
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

const renderLucideSvg = (iconDef: IconNode, size = 14, color = 'currentColor'): string => {
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
 * @param value - The score value (0 to maxScore), or null if no data
 * @param colors - Color palette to use for bar color
 * @param maxScore - Maximum possible score
 * @returns HTML string for the bar chart or "No data" message
 */
const createScoreBar = (
  value: number | string | null | undefined,
  colors: string[] = badColors,
  maxScore = MAX_SCORE,
): string => {
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

  const clamped = Math.max(0, Math.min(maxScore, num))
  const percentage = Math.round((clamped / maxScore) * 100)
  const barColor = scoreToColor(clamped, colors, maxScore)

  return `
    <div style="background: rgba(0, 0, 0, 0.06); border-radius: 3px; height: 16px; overflow: hidden; position: relative; margin-top: 4px;">
      <div style="background: ${barColor}; height: 100%; width: ${percentage}%; transition: width 0.3s ease;"></div>
      <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; color: #363636;">
        ${num.toFixed(1)}/${maxScore}
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
  colors: string[] = badColors,
  maxScore = MAX_SCORE,
  isRawHtml = false,
): string => {
  const formattedValue =
    typeof value === 'number' ? value.toFixed(2) : isRawHtml ? String(value) : escapeHtml(value)
  let html = `<div style="margin-bottom: 12px;">
    <div style="display: flex; align-items: center; margin-bottom: 2px;">${iconSvg ?? ''}<strong>${escapeHtml(label)}:</strong>&nbsp;<span>${formattedValue}</span></div>`

  if (scoreValue !== undefined) {
    html += createScoreBar(scoreValue, colors, maxScore)
  }

  html += '</div>'
  return html
}

/**
 * Creates a formatted HTML popup for a GeoJSON feature
 * @param feature - The GeoJSON feature
 * @returns HTML string for the popup
 */
export const createFeaturePopup = (
  feature: GeoJsonFeature,
  colors: string[] = badColors,
  maxScore = MAX_SCORE,
): string => {
  if (!feature.properties) return ''

  const props = feature.properties
  let html = '<div style="min-width: 220px; font-family: sans-serif;">'

  // Name
  if ('name' in props) {
    html += `<div style="margin-bottom: 12px; display: flex; align-items: center;">${renderLucideSvg(MapPin, 14, '#4a4a4a')}<strong>Name:</strong>&nbsp;<span>${escapeHtml(props.name)}</span></div>`
  }

  // Lanes
  if ('lanes_int' in props) {
    html += `<div style="margin-bottom: 12px;"><strong>Lanes:</strong>&nbsp;<span>${escapeHtml(props.lanes_int)}</span></div>`
  }

  // Separation Level with score
  if ('separation_level' in props && props.separation_level !== undefined) {
    html += createFieldWithScore(
      'Separation Level',
      props.separation_level,
      props.separation_level_score ?? null,
      renderLucideSvg(Shield, 14, '#3273dc'),
      colors,
      maxScore,
    )
  }

  // Street Classification with score
  if ('street_classification' in props && props.street_classification !== undefined) {
    html += createFieldWithScore(
      'Street Classification',
      props.street_classification,
      props.street_classification_score ?? null,
      renderLucideSvg(Car, 14, '#e67e22'),
      colors,
      maxScore,
    )
  }

  // Max Speed with score
  const rawSpeed = props.maxspeed_int
  const hasSpeed =
    rawSpeed !== undefined &&
    rawSpeed !== null &&
    rawSpeed !== '' &&
    !isNaN(Number(rawSpeed)) &&
    Number(rawSpeed) > 0

  const speedDisplay = hasSpeed
    ? `${escapeHtml(rawSpeed)} mph`
    : `<span style="font-style: italic; color: #888;">unknown</span>`

  html += createFieldWithScore(
    'Max Speed',
    speedDisplay,
    hasSpeed ? (props.maxspeed_int_score ?? null) : null,
    renderLucideSvg(Gauge, 14, '#48c774'),
    colors,
    maxScore,
    true,
  )

  // Composite Score with bar chart
  if ('composite_score' in props) {
    const rawScore = props.composite_score
    const numScore =
      typeof rawScore === 'number'
        ? rawScore
        : rawScore !== null && rawScore !== undefined
          ? parseFloat(String(rawScore))
          : null

    const compositeIcon = renderLucideSvg(Layers, 14, '#363636')
    if (numScore !== null && !isNaN(numScore)) {
      html += `<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(0, 0, 0, 0.1);">
        <div style="display: flex; align-items: center; margin-bottom: 2px;">${compositeIcon}<strong>Composite Score:</strong>&nbsp;<span>${numScore.toFixed(2)}</span></div>`
      html += createScoreBar(numScore, colors, maxScore)
      html += '</div>'
    } else {
      // Show "No data" for composite score
      html += `<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(0, 0, 0, 0.1);">
        <div style="display: flex; align-items: center; margin-bottom: 2px;">${compositeIcon}<strong>Composite Score:</strong>&nbsp;<span style="font-style: italic; color: #999;">No data</span></div>`
      html += createScoreBar(null, colors, maxScore)
      html += '</div>'
    }
  }

  html += '</div>'
  return html
}
