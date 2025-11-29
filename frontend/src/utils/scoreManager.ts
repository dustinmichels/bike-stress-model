/**
 * Score Manager
 * Handles calculation of composite scores for street segments
 */

export interface ScoreWeights {
  maxspeed_int_score: number
  separation_level_score: number
  street_classification_score: number
  lanes_int_score: number
}

export interface StreetProperties {
  maxspeed_int_score?: number
  separation_level_score?: number
  street_classification_score?: number
  lanes_int_score?: number
  composite_score?: number
  [key: string]: any
}

export interface GeoJsonFeature {
  type: string
  properties: StreetProperties
  geometry: any
}

export interface GeoJsonData {
  type: string
  features: GeoJsonFeature[]
}

/**
 * Default weights for score calculation
 * These match the ModelComponent default percentages:
 * - Separation level: 50%
 * - Speed (maxspeed): 25%
 * - Busyness (street_classification): 25%
 * - Lanes: 0% (not shown in ModelComponent)
 */
export const defaultWeights: ScoreWeights = {
  separation_level_score: 0.5, // 50%
  maxspeed_int_score: 0.25, // 25%
  street_classification_score: 0.25, // 25%
  lanes_int_score: 0, // 0% (not in model)
}

/**
 * Calculate composite score for a single feature using weighted average
 * The weights represent the percentage/proportion each component contributes
 */
export const calculateCompositeScore = (
  properties: StreetProperties,
  weights: ScoreWeights = defaultWeights,
): number => {
  const {
    maxspeed_int_score = 0,
    separation_level_score = 0,
    street_classification_score = 0,
    lanes_int_score = 0,
  } = properties

  // Calculate weighted sum
  const weightedSum =
    maxspeed_int_score * weights.maxspeed_int_score +
    separation_level_score * weights.separation_level_score +
    street_classification_score * weights.street_classification_score +
    lanes_int_score * weights.lanes_int_score

  // Calculate total weight (should sum to 1.0 for normalized weights)
  const totalWeight =
    weights.maxspeed_int_score +
    weights.separation_level_score +
    weights.street_classification_score +
    weights.lanes_int_score

  // Return weighted average
  // If total weight is 0, return 0; otherwise divide by total to normalize
  return totalWeight > 0 ? weightedSum / totalWeight : 0
}

/**
 * Recalculate composite scores for all features in a GeoJSON dataset
 */
export const recalculateAllScores = (
  geojsonData: GeoJsonData,
  weights: ScoreWeights = defaultWeights,
): GeoJsonData => {
  // Deep copy to avoid mutating original
  const updatedData = JSON.parse(JSON.stringify(geojsonData))

  // Update each feature's composite score
  updatedData.features.forEach((feature: GeoJsonFeature) => {
    feature.properties.composite_score = calculateCompositeScore(feature.properties, weights)
  })

  return updatedData
}

/**
 * Get statistics about scores in the dataset
 */
export const getScoreStats = (geojsonData: GeoJsonData) => {
  const scores = geojsonData.features
    .map((f) => f.properties.composite_score)
    .filter((score): score is number => score !== undefined)

  if (scores.length === 0) {
    return { min: 0, max: 0, avg: 0, count: 0 }
  }

  return {
    min: Math.min(...scores),
    max: Math.max(...scores),
    avg: scores.reduce((sum, score) => sum + score, 0) / scores.length,
    count: scores.length,
  }
}

/**
 * Convert percentage-based weights (0-100) to normalized weights (0-1)
 * Useful for integrating with ModelComponent which uses percentages
 *
 * @param percentages - Object with percentage values (should sum to 100)
 * @returns Normalized weights (will sum to 1.0)
 */
export const percentagesToWeights = (percentages: {
  separation_level: number
  speed: number
  busyness: number
}): ScoreWeights => {
  const total = percentages.separation_level + percentages.speed + percentages.busyness

  // Normalize to ensure they sum to 1.0
  const normalize = total > 0 ? 100 / total : 1

  return {
    separation_level_score: (percentages.separation_level / 100) * normalize,
    maxspeed_int_score: (percentages.speed / 100) * normalize,
    street_classification_score: (percentages.busyness / 100) * normalize,
    lanes_int_score: 0, // Not included in the model
  }
}
