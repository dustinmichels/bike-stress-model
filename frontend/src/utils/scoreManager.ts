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
 * Default weights for score calculation (equal weighting)
 */
export const defaultWeights: ScoreWeights = {
  maxspeed_int_score: 1,
  separation_level_score: 1,
  street_classification_score: 1,
  lanes_int_score: 1,
}

/**
 * Calculate composite score for a single feature
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

  // Calculate total weight
  const totalWeight =
    weights.maxspeed_int_score +
    weights.separation_level_score +
    weights.street_classification_score +
    weights.lanes_int_score

  // Return weighted average
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
