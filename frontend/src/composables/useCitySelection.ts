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

  const formatCityParam = (city: string): string => `${city.toLowerCase()},ma`

  const isCanonicalUrl = (city: string): boolean => {
    if (typeof window === 'undefined') return true
    const raw = new URLSearchParams(window.location.search).get('city')
    return raw === formatCityParam(city)
  }

  const syncUrl = (city: string, mode: 'push' | 'replace' = 'push') => {
    if (typeof window === 'undefined') return
    const params = new URLSearchParams(window.location.search)
    params.set('city', formatCityParam(city))
    const queryString = `?${params.toString().replace(/%2C/gi, ',')}`
    const targetUrl = `${window.location.pathname}${queryString}${window.location.hash}`
    const currentUrl = `${window.location.pathname}${window.location.search}${window.location.hash}`
    if (currentUrl === targetUrl) return

    if (mode === 'replace') {
      window.history.replaceState({ city }, '', targetUrl)
    } else {
      window.history.pushState({ city }, '', targetUrl)
    }
  }

  const currCity = shallowRef<string>(parseCityFromUrl() ?? defaultCity)

  // Redirect on load if base URL (no city param), invalid city param, or non-canonical format
  if (typeof window !== 'undefined') {
    if (parseCityFromUrl() === null || !isCanonicalUrl(currCity.value)) {
      syncUrl(currCity.value, 'replace')
    }
  }

  const onPopState = () => {
    const cityFromUrl = parseCityFromUrl()
    if (cityFromUrl) {
      if (cityFromUrl !== currCity.value) {
        currCity.value = cityFromUrl
      }
      if (!isCanonicalUrl(cityFromUrl)) {
        syncUrl(cityFromUrl, 'replace')
      }
    } else {
      if (currCity.value !== defaultCity) {
        currCity.value = defaultCity
      }
      syncUrl(defaultCity, 'replace')
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
      syncUrl(newCity, 'push')
    }
  })

  return {
    cities,
    currCity,
    parseCityFromUrl,
  }
}
