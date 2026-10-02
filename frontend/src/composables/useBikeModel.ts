import { BIKE_INFRASTRUCTURE_MODEL } from '@/data/bikeData'
import type { BikeInfrastructureModel, GeoJsonData, ModelWeights } from '@/types'
import { badColors, goodColors, scoreToColor } from '@/utils/colorScale'
import { calculateAllScores } from '@/utils/scoreCalculator'
import {
  computed,
  ref,
  shallowRef,
  toValue,
  watch,
  type ComputedRef,
  type MaybeRefOrGetter,
  type Ref,
  type ShallowRef,
} from 'vue'

export const CITY_FILE_MAP: Record<string, string> = {
  Somerville: 'somerville_streets.geojson',
  Cambridge: 'cambridge_streets.geojson',
  Everett: 'everett_streets.geojson',
  Malden: 'malden_streets.geojson',
}

export interface UseBikeModelOptions {
  city: MaybeRefOrGetter<string>
  useGoodColors?: MaybeRefOrGetter<boolean>
}

export interface UseBikeModelReturn {
  modelConfig: Ref<BikeInfrastructureModel>
  modelWeights: ComputedRef<ModelWeights>
  geojsonData: ShallowRef<GeoJsonData | null>
  enrichedGeoJson: ComputedRef<GeoJsonData | null>
  loading: ShallowRef<boolean>
  error: ShallowRef<string | null>
  handleWeightsChanged: (weights: ModelWeights) => void
  handleUpdateScore: (field: string, category: string, score: number) => void
  resetFieldScores: (field: string) => void
  resetAllScores: () => void
  loadGeoJsonForCity: (city: string) => Promise<void>
}

/**
 * Manages bike infrastructure scoring model configuration, weights, and
 * GeoJSON data loading & enrichment.
 */
export function useBikeModel(options: UseBikeModelOptions): UseBikeModelReturn {
  const modelConfig = ref<BikeInfrastructureModel>(
    JSON.parse(JSON.stringify(BIKE_INFRASTRUCTURE_MODEL)),
  )

  const modelWeights = computed<ModelWeights>(() => ({
    separation_level: modelConfig.value.separation_level.weight,
    speed: modelConfig.value.speed_limit.weight,
    busyness: modelConfig.value.street_classification.weight,
  }))

  const geojsonData = shallowRef<GeoJsonData | null>(null)
  const loading = shallowRef(false)
  const error = shallowRef<string | null>(null)
  let activeAbortController: AbortController | null = null

  const loadGeoJsonForCity = async (city: string): Promise<void> => {
    // Abort previous pending fetch if any
    activeAbortController?.abort()
    const controller = new AbortController()
    activeAbortController = controller

    const fileName = CITY_FILE_MAP[city]
    if (!fileName) {
      error.value = `No GeoJSON file configured for city: ${city}`
      geojsonData.value = null
      return
    }

    loading.value = true
    error.value = null

    try {
      const response = await fetch(import.meta.env.BASE_URL + fileName, {
        signal: controller.signal,
      })
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`)
      }
      const data: GeoJsonData = await response.json()
      // Guard against stale response if another city was requested
      if (controller.signal.aborted || toValue(options.city) !== city) {
        return
      }
      geojsonData.value = data
    } catch (e: unknown) {
      if (e instanceof DOMException && e.name === 'AbortError') {
        return
      }
      const message = e instanceof Error ? e.message : String(e)
      error.value = `Error loading GeoJSON for ${city}: ${message}`
      console.error(error.value, e)
    } finally {
      if (!controller.signal.aborted) {
        loading.value = false
      }
    }
  }

  // Enriched GeoJSON derives dynamically from raw data, model weights, and score tables.
  // Performs shallow feature copies to keep coordinates by reference for maximum performance.
  const enrichedGeoJson = computed<GeoJsonData | null>(() => {
    const raw = geojsonData.value
    if (!raw) return null

    const isGoodColors = options.useGoodColors ? toValue(options.useGoodColors) : true
    const palette = isGoodColors ? goodColors : badColors
    const config = modelConfig.value
    const weights = modelWeights.value

    const features = raw.features.map((feature, index) => {
      const scores = calculateAllScores(feature.properties, config, weights)
      const color = scoreToColor(scores.composite_score, palette)

      return {
        ...feature,
        id: index,
        properties: {
          ...feature.properties,
          ...scores,
          color,
          __id: index,
        },
      }
    })

    return {
      ...raw,
      features,
    }
  })

  const handleWeightsChanged = (weights: ModelWeights) => {
    modelConfig.value.separation_level.weight = weights.separation_level
    modelConfig.value.speed_limit.weight = weights.speed
    modelConfig.value.street_classification.weight = weights.busyness
  }

  const handleUpdateScore = (field: string, category: string, score: number) => {
    const fieldConfig = modelConfig.value[field as keyof BikeInfrastructureModel]
    if (fieldConfig?.categories[category]) {
      fieldConfig.categories[category].score = score
    }
  }

  const resetFieldScores = (field: string) => {
    const originalField = BIKE_INFRASTRUCTURE_MODEL[field as keyof typeof BIKE_INFRASTRUCTURE_MODEL]
    const currentField = modelConfig.value[field as keyof BikeInfrastructureModel]
    if (originalField?.categories && currentField?.categories) {
      for (const [key, cat] of Object.entries(originalField.categories)) {
        if (currentField.categories[key]) {
          currentField.categories[key].score = cat.score
        }
      }
    }
  }

  const resetAllScores = () => {
    modelConfig.value = JSON.parse(JSON.stringify(BIKE_INFRASTRUCTURE_MODEL))
  }

  // Automatically fetch data whenever the active city changes
  watch(
    () => toValue(options.city),
    (newCity) => {
      if (newCity) {
        loadGeoJsonForCity(newCity)
      }
    },
    { immediate: true },
  )

  return {
    modelConfig,
    modelWeights,
    geojsonData,
    enrichedGeoJson,
    loading,
    error,
    handleWeightsChanged,
    handleUpdateScore,
    resetFieldScores,
    resetAllScores,
    loadGeoJsonForCity,
  }
}
