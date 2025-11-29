export interface CategoryData {
  score: number
  img: string
  notes: string
}

export interface ParameterData {
  img: string
  link?: string
  notes: string
  categories: Record<string, CategoryData>
}

export interface BikeInfrastructureData {
  separation_level: ParameterData
  street_classification: ParameterData
  speed_limit: ParameterData
}

export const BIKE_INFRASTRUCTURE_DATA: BikeInfrastructureData = {
  separation_level: {
    img: '',
    link: 'https://wiki.openstreetmap.org/wiki/Key:cycleway',
    notes:
      'Measures the physical separation between cyclists and motor vehicle traffic. Higher scores indicate better protection and safety for cyclists.',
    categories: {
      separate: {
        score: 0,
        img: '',
        notes: 'Completely separated infrastructure - no interaction with motor vehicle traffic',
      },
      track: {
        score: 1,
        img: '',
        notes:
          'Physically separated bike track (protected bike lane), sometimes also used for buffered lanes',
      },
      lane_buffered: {
        score: 2,
        img: '',
        notes: 'Bike lane with a painted buffer zone between cyclists and motor vehicles',
      },
      lane: {
        score: 3,
        img: '',
        notes: 'Dedicated bike lane painted on the road, not physically separated from traffic',
      },
      share_busway: {
        score: 4,
        img: '',
        notes: 'Cyclists share a dedicated bus lane or transitway',
      },
      shared_lane: {
        score: 4.5,
        img: '',
        notes: 'Cyclists share a lane with motor vehicle traffic (sharrows, marked shared lanes)',
      },
      none: {
        score: 5,
        img: '',
        notes: 'No separation - cyclists share the road directly with motor vehicles',
      },
    },
  },

  street_classification: {
    img: '',
    notes:
      'Evaluates the type of street and its primary function. Lower-traffic streets and dedicated paths score higher.',
    categories: {
      dedicated_path: {
        score: 0,
        img: '',
        notes:
          'Path dedicated exclusively to cyclists and pedestrians, separate from the road network',
      },
      residential: {
        score: 2,
        img: '',
        notes: 'Low-traffic residential streets with minimal through traffic',
      },
      'medium-capacity': {
        score: 4,
        img: 'https://wiki.openstreetmap.org/w/images/4/42/Rendering-highway_secondary_neutral.png',
        notes: 'Arterial roads or collectors with moderate to high traffic volumes',
      },
      motorway: {
        score: 5,
        img: 'https://wiki.openstreetmap.org/w/images/6/6a/Rendering-highway_motorway_neutral.png',
        notes: 'High-speed highways or motorways (generally prohibited for cyclists)',
      },
    },
  },

  speed_limit: {
    img: '',
    notes:
      'Speed limits of adjacent motor vehicle traffic. Lower speeds create safer environments for cycling.',
    categories: {
      '20_mph_or_less': {
        score: 0,
        img: '',
        notes: 'Maximum speed limit of 20 mph or less - safest for cycling',
      },
      '25_mph': {
        score: 1,
        img: '',
        notes: 'Maximum speed limit of 25 mph',
      },
      '30_mph': {
        score: 3,
        img: '',
        notes: 'Maximum speed limit of 30 mph',
      },
      '40_mph': {
        score: 4,
        img: '',
        notes: 'Maximum speed limit of 40 mph',
      },
      '50_mph': {
        score: 4.5,
        img: '',
        notes: 'Maximum speed limit of 50 mph',
      },
      over_50_mph: {
        score: 5,
        img: '',
        notes: 'Speed limit over 50 mph - least safe for cycling',
      },
    },
  },
}

export interface ModelWeights {
  separation_level: number
  speed: number
  busyness: number
}

export const DEFAULT_WEIGHTS: ModelWeights = {
  separation_level: 50,
  speed: 25,
  busyness: 25,
}
