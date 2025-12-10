import type { BikeInfrastructureModel } from '@/types'

/**
 * BIKE INFRASTRUCTURE SCORING MODEL
 *
 * This model defines the scoring categories and weights for evaluating bike infrastructure.
 *
 * EXPECTED GEOJSON FIELDS:
 * Your GeoJSON features should have these properties:
 * - separation_level: string (e.g., "lane", "track", "none", "shared_lane")
 * - street_classification: string (e.g., "residential", "medium-capacity", "dedicated_path")
 * - maxspeed_int: number (integer speed limit, e.g., 25, 30, 40)
 *
 * The scoreCalculator will:
 * 1. Read these fields from your GeoJSON
 * 2. Look up the score for each category in this model
 * 3. Calculate a weighted composite score based on the model weights
 */

export const BIKE_INFRASTRUCTURE_MODEL: BikeInfrastructureModel = {
  // 1️⃣ Separation Level (60%)
  separation_level: {
    weight: 60,
    displayLabel: 'Separation Level',
    defaultCategory: 'none',
    img: '',
    link: 'https://wiki.openstreetmap.org/wiki/Key:cycleway',
    notes: '',
    categories: {
      separate: {
        score: 0,
        displayLabel: 'Completely Separated',
        img: '',
        notes: 'Completely separated infrastructure',
      },
      track: {
        score: 1,
        displayLabel: 'Protected Track',
        img: '',
        notes: 'Physically separated bike track (protected bike lane)',
      },
      lane_buffered: {
        score: 1.5,
        displayLabel: 'Buffered Bike Lane',
        img: '',
        notes:
          'Could be a painted buffer or physical buffer (e.g., bollards) separating bike lane from traffic. In the data, sometimes used interchangeably with "track".',
      },
      lane: {
        score: 2.5,
        displayLabel: 'Painted Bike Lane',
        img: '',
        notes: 'Dedicated bike lane painted on the road, not physically separated from traffic',
      },
      share_busway: {
        score: 3,
        displayLabel: 'Shared Bus Lane',
        img: '',
        notes: 'Cyclists share a dedicated lane with buses',
      },
      shared_lane: {
        score: 3.5,
        displayLabel: 'Shared Lane',
        img: '',
        notes: 'Cyclists share a lane with motor vehicle traffic (sharrows, marked shared lanes)',
      },
      none: {
        score: 4,
        displayLabel: 'No Separation',
        img: '',
        notes: 'No separation & probably no markings',
      },
    },
  },

  // 2️⃣ Street Classification / Busyness (20%)
  street_classification: {
    weight: 20,
    displayLabel: 'Busyness',
    defaultCategory: 'residential',
    img: '',
    notes:
      'Evaluates the type of street and its primary function. Lower-traffic streets and dedicated paths score higher.',
    categories: {
      dedicated_path: {
        score: 0,
        displayLabel: 'Dedicated Path',
        img: '',
        notes:
          'Path dedicated exclusively to cyclists and pedestrians, separate from the road network',
      },
      residential: {
        score: 2,
        displayLabel: 'Residential Street',
        img: '',
        notes: 'Low-traffic residential streets with minimal through traffic',
      },
      'medium-capacity': {
        score: 3,
        displayLabel: 'Medium-Capacity Road',
        notes: 'Arterial roads or collectors with moderate to high traffic volumes',
      },
      motorway: {
        score: 4,
        displayLabel: 'Motorway',
        notes: 'High-speed highways or motorways (generally prohibited for cyclists)',
      },
    },
  },

  // 3️⃣ Speed Limit (20%)
  speed_limit: {
    weight: 20,
    displayLabel: 'Speed Limit',
    defaultCategory: 25, // Integer value, will be mapped to '25_mph' category
    img: '',
    notes: '',
    categories: {
      '20_mph_or_less': {
        score: 0,
        displayLabel: '≤ 20 mph',
        img: '',
        notes: '',
      },
      '25_mph': {
        score: 1,
        displayLabel: '25 mph',
        img: '',
        notes: '',
      },
      '30_mph': {
        score: 2.5,
        displayLabel: '30 mph',
        img: '',
        notes: '',
      },
      '40_mph': {
        score: 3,
        displayLabel: '40 mph',
        img: '',
        notes: '',
      },
      '50_mph': {
        score: 3.5,
        displayLabel: '50 mph',
        img: '',
        notes: '',
      },
      over_50_mph: {
        score: 4,
        displayLabel: '> 50 mph',
        img: '',
        notes: '',
      },
    },
  },
}
