import type { ColorMode } from '@/types'

export const MAX_SCORE = 4

export const goodColors = [
  '#2ca25f', // deep green
  '#88b14b', // muted green-yellow
  '#c4c25a', // soft yellow
  '#e6e3a0', // very pale yellow
  '#ffffff', // white
]

export const badColors = ['#fff7ec', '#fee8c8', '#fdbb84', '#e34a33', '#b30000']

export const safetyColors = [
  '#2ca25f', // green (safe - 0)
  '#88b14b', // green-yellow (1)
  '#d97706', // amber/yellow (2)
  '#e34a33', // orange (3)
  '#b30000', // red (unsafe - 4)
]

export const MISSING_DATA_COLOR = '#808080' // Grey for missing data

export const colorPalettes: Record<ColorMode, string[]> = {
  safety: goodColors,
  'safety-risk': safetyColors,
  risk: badColors,
}

/**
 * Maps a numeric score (0 to MAX_SCORE) to a color in the given palette.
 * Returns MISSING_DATA_COLOR if score is null, undefined, or NaN.
 */
export const scoreToColor = (
  score: number | null | undefined,
  colors: string[] = badColors,
  maxScore: number = MAX_SCORE,
): string => {
  if (score === null || score === undefined || isNaN(score)) {
    return MISSING_DATA_COLOR
  }
  const clamped = Math.max(0, Math.min(maxScore, score))
  const normalized = maxScore > 0 ? clamped / maxScore : 0
  const idx = Math.min(Math.floor(normalized * colors.length), colors.length - 1)
  return colors[idx] ?? colors[0] ?? MISSING_DATA_COLOR
}
