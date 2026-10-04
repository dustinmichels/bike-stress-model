## Oct 2, 2026

### Backend & Data Pipeline

- **Pipeline CLI (`main.py`)**: Added root automation pipeline using OSMnx and Rich to extract OSM bike networks, run stress models (speed, separation level, highway classification, lanes), calculate weighted composite stress scores, export GeoJSON/GPKG/CSV, and copy output to `frontend/public`.
- **Monorepo Flattening**: Merged `backend/` into repository root (`src/`, `tests/`, `notebooks/`, `pyproject.toml`, `uv.lock`); deleted obsolete files (`backend/api.py`, `crash.py`, `crash_local.py`, old `main.py`, duck/crash notebooks) and Render deployment config.
- **Python Modernization & Tests**: Updated typings to PEP 604 unions (`|`), replaced manual zip edge slicing with `itertools.pairwise` in `src/route.py`, and added unit tests in `tests/test_main.py`.
- **Tooling**: Added `.oxfmtrc.json` and `pyrightconfig.json`; updated `mise.toml`.

### Frontend Architecture

- **Composables**:
  - `useBikeModel`: Encapsulated model configuration, custom weight state, GeoJSON loading with `AbortController` cancellation, and dynamic client-side score recalculation.
  - `useCitySelection`: Managed city state with bidirectional URL query synchronization (`?city=<name>,ma`) and browser `popstate` history navigation.
- **Bundle Splitting**: Lazy-loaded `ExportMapModal` via `defineAsyncComponent` to keep Mermaid out of the initial bundle.
- **Scoring & Types**: Added category aliases (`SEPARATION_LEVEL_ALIASES`) and deduplicated warning logging in `scoreCalculator.ts`; updated `types.ts` to handle nullable score values and typed geometry.

### Mapping & UI

- **MapLibre GL JS Migration**: Replaced Leaflet with `maplibre-gl` using an external web worker (`maplibre-gl-worker.mjs`) for vector rendering and layer interactions.
- **Popups (`tooltipUtils.ts`)**: Built MapLibre HTML popups featuring Lucide SVG icons, score bars, normalized color scales, and HTML escaping.
- **Component Refactors**:
  - Replaced FontAwesome and raw SVGs across all components with `@lucide/vue` icons.
  - Refactored `AboutComponent.vue` with an inline city dropdown using Vue 3.4+ `defineModel`.
  - Teleported `SettingsModal.vue` to `body` with direct prop reactivity.
  - Updated `ModelSliders.vue` handle drag behaviors and external synchronization.

### Data & Assets

- Added Malden network dataset (`malden_streets.geojson`) and regenerated Cambridge, Everett, and Somerville network files.
- Updated application icons, favicons, and web manifest.
