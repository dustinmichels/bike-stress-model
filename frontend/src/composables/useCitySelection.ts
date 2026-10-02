import { onMounted, onUnmounted, shallowRef, watch } from 'vue'

export const DEFAULT_CITIES = ['Somerville', 'Cambridge', 'Everett', 'Malden'] as const

export interface UseCitySelectionOptions {
  cities?: readonly string[]
  defaultCity?: string
}

/**
 * Manages city selection and synchronizes with browser URL query parameter (?city=...)
 * and browser history (popstate).
 */
export function useCitySelection(options: UseCitySelectionOptions = {}) {
  const cities = options.cities ?? DEFAULT_CITIES
  const defaultCity = options.defaultCity ?? cities[0] ?? 'Somerville'

  const parseCityFromUrl = (): string | null => {
    if (typeof window === 'undefined') return null
    const raw = new URLSearchParams(window.location.search).get('city')
    if (!raw) return null
    const cleaned = raw.split(/[,-]/)[0]?.trim().toLowerCase()
    if (!cleaned) return null
    return cities.find((c) => c.toLowerCase() === cleaned) ?? null
  }

  const currCity = shallowRef<string>(parseCityFromUrl() ?? defaultCity)

  const onPopState = () => {
    const cityFromUrl = parseCityFromUrl() ?? defaultCity
    if (cityFromUrl !== currCity.value) {
      currCity.value = cityFromUrl
    }
  }

  onMounted(() => {
    window.addEventListener('popstate', onPopState)
  })

  onUnmounted(() => {
    window.removeEventListener('popstate', onPopState)
  })

  watch(currCity, (newCity) => {
    if (typeof window === 'undefined') return
    if (parseCityFromUrl() !== newCity) {
      const params = new URLSearchParams(window.location.search)
      params.set('city', `${newCity.toLowerCase()},ma`)
      const queryString = `?${params.toString().replace(/%2C/gi, ',')}`
      window.history.pushState(
        { city: newCity },
        '',
        `${window.location.pathname}${queryString}${window.location.hash}`,
      )
    }
  })

  return {
    cities,
    currCity,
    parseCityFromUrl,
  }
}
