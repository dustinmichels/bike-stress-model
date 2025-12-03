import type { BikeInfrastructureModel, ModelWeights, StreetProperties } from '@/types'

/**
 * Calculate the separation level score for a street
 * Returns null if data is missing
 */
export const calculateSeparationScore = (
  properties: StreetProperties,
  modelConfig: BikeInfrastructureModel,
): number | null => {
  const category = properties.separation_level

  // Return null if data is missing
  if (!category) {
    return null
  }

  const score = modelConfig.separation_level.categories[category]?.score

  if (score === undefined) {
    console.warn(`Unknown separation_level category '${category}'`)
    return null
  }

  return score
}

/**
 * Calculate the street classification score for a street
 * Returns null if data is missing
 */
export const calculateStreetClassificationScore = (
  properties: StreetProperties,
  modelConfig: BikeInfrastructureModel,
): number | null => {
  const category = properties.street_classification

  // Return null if data is missing
  if (!category) {
    return null
  }

  const score = modelConfig.street_classification.categories[category]?.score

  if (score === undefined) {
    console.warn(`Unknown street_classification category '${category}'`)
    return null
  }

  return score
}

/**
 * Calculate the speed limit score for a street
 * Returns null if data is missing
 */
export const calculateSpeedScore = (
  properties: StreetProperties,
  modelConfig: BikeInfrastructureModel,
): number | null => {
  const maxspeedValue = properties.maxspeed_int

  // Helper function to map speed to category
  const speedToCategory = (speed: number): string => {
    if (speed <= 20) return '20_mph_or_less'
    if (speed <= 25) return '25_mph'
    if (speed <= 30) return '30_mph'
    if (speed <= 40) return '40_mph'
    if (speed <= 50) return '50_mph'
    return 'over_50_mph'
  }

  // Return null if data is missing
  if (maxspeedValue === undefined || maxspeedValue === null) {
    return null
  }

  // Convert to number if it's a string
  const speed = typeof maxspeedValue === 'number' ? maxspeedValue : parseInt(String(maxspeedValue))

  if (isNaN(speed)) {
    console.warn(`Invalid maxspeed_int value '${maxspeedValue}'`)
    return null
  }

  const category = speedToCategory(speed)
  const score = modelConfig.speed_limit.categories[category]?.score

  if (score === undefined) {
    console.warn(`Unknown speed category '${category}'`)
    return null
  }

  return score
}

/**
 * Calculate the composite score using weighted average
 * Only includes available (non-null) scores in the calculation
 * Returns null if all scores are missing
 */
export const calculateCompositeScore = (
  separationScore: number | null,
  streetClassScore: number | null,
  speedScore: number | null,
  weights: ModelWeights,
): number | null => {
  // Collect available scores with their weights
  const availableScores: { score: number; weight: number }[] = []

  if (separationScore !== null) {
    availableScores.push({ score: separationScore, weight: weights.separation_level })
  }
  if (speedScore !== null) {
    availableScores.push({ score: speedScore, weight: weights.speed })
  }
  if (streetClassScore !== null) {
    availableScores.push({ score: streetClassScore, weight: weights.busyness })
  }

  // If no scores are available, return null
  if (availableScores.length === 0) {
    return null
  }

  // Calculate total weight of available scores
  const totalWeight = availableScores.reduce((sum, item) => sum + item.weight, 0)

  if (totalWeight === 0) {
    return null
  }

  // Calculate weighted average using only available scores
  const weightedSum = availableScores.reduce((sum, item) => sum + item.score * item.weight, 0)

  return weightedSum / totalWeight
}

/**
 * Calculate all scores for a single street feature
 */
let calculationCount = 0

export const calculateAllScores = (
  properties: StreetProperties,
  modelConfig: BikeInfrastructureModel,
  weights: ModelWeights,
): {
  separation_level_score: number | null
  street_classification_score: number | null
  maxspeed_int_score: number | null
  composite_score: number | null
} => {
  const separationScore = calculateSeparationScore(properties, modelConfig)
  const streetClassScore = calculateStreetClassificationScore(properties, modelConfig)
  const speedScore = calculateSpeedScore(properties, modelConfig)
  const compositeScore = calculateCompositeScore(
    separationScore,
    streetClassScore,
    speedScore,
    weights,
  )

  // Debug logging for the first 5 features
  if (calculationCount < 5) {
    console.log(`Calculation ${calculationCount + 1}:`, {
      input: {
        separation_level: properties.separation_level,
        street_classification: properties.street_classification,
        maxspeed_int: properties.maxspeed_int,
      },
      intermediateScores: {
        separation: separationScore,
        streetClass: streetClassScore,
        speed: speedScore,
      },
      weights,
      finalComposite: compositeScore,
      missingData: {
        separation: separationScore === null,
        streetClass: streetClassScore === null,
        speed: speedScore === null,
      },
    })
    calculationCount++
  }

  return {
    separation_level_score: separationScore,
    street_classification_score: streetClassScore,
    maxspeed_int_score: speedScore,
    composite_score: compositeScore,
  }
}
