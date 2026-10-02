/// <reference types="vite/client" />

import type { Map as MapLibreMap } from 'maplibre-gl'

declare global {
  interface Window {
    _map?: MapLibreMap
  }
}
