// Type definitions for the bike infrastructure scoring system

export interface CategoryData {
  score: number
  displayLabel: string
  img?: string
  notes: string
}

export interface ParameterData {
  weight: number
  displayLabel: string
  img?: string
  link?: string
  notes: string
  defaultCategory?: string | number // Default category to use when data is missing
  categories: Record<string, CategoryData>
}

export interface BikeInfrastructureModel {
  separation_level: ParameterData
  street_classification: ParameterData
  speed_limit: ParameterData
}

export interface ModelWeights {
  separation_level: number
  speed: number
  busyness: number
}

export interface StreetProperties {
  // Category fields from GeoJSON
  separation_level?: string // e.g., "lane", "track", "none"
  street_classification?: string // e.g., "residential", "medium-capacity"
  maxspeed_int?: number | string // Integer speed value (e.g., 25, 30, 40)

  // Other properties
  name?: string

  // Computed scores (will be calculated dynamically)
  separation_level_score?: number
  street_classification_score?: number
  maxspeed_int_score?: number
  composite_score?: number

  [key: string]: unknown
}

export interface GeoJsonGeometry {
  type: string
  coordinates: unknown
}

export interface GeoJsonFeature {
  id?: string | number
  type: string
  properties: StreetProperties
  geometry: GeoJsonGeometry
}
export interface GeoJsonData {
  type: string
  features: GeoJsonFeature[]
}
