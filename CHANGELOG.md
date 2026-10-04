## Unreleased

### Frontend

- **Map loading state**: Lazy-load MapLibre so the page controls render immediately, and show a map-area spinner until both the map and city data are ready.
- **About modal**: Replaced the external About link with a responsive, keyboard-accessible model guide covering the 0–4 stress score, default weights, map controls, assumptions, known data limitations, and links to the original story map and course code.
- **Map resource hints**: Preconnect to the Carto style and tile origins while the application shell loads, reducing cold-start DNS and TLS latency before MapLibre requests the basemap.

### Backend & Data Pipeline

- **Per-city residential speed defaults**: `PLACES` in `main.py` is now a list of pydantic `Place` models (`name`, `residential_default_mph`), and `prepare_data_for_place` takes a `Place`. Residential streets without a posted `maxspeed` default to 20 mph in Somerville and Cambridge and 25 mph in Everett and Malden. The default now covers every `residential`-class edge (`residential`, `living_street`, `service`, `unclassified`, `track`, list-valued `highway`); before, only `highway=residential` got it, and always at 20 mph. Arterials without a posted speed stay null. Removed the dead `DEFAULT_SPEED_LIMIT` and the unused frontend `defaultCategory` fields.
- **Typed pipeline config (pydantic)**: `Place` gained `city`/`slug` properties; `save_data_for_place` and `copy_to_frontend` take `Place` objects instead of name strings. The summary table rows are `CitySummary` models. Composite weights are a `CompositeWeights` model (each ≥ 0, at least one > 0; they are renormalized per edge, so they need not sum to 1).
- **Validated score tables**: New `src/stressmodel/scoring.py` (`Score` 0–4, `Tier`, `Tiers` with ascending bounds). `SPEED_RANKINGS`/`LANES_RANKINGS` became `SPEED_TIERS`/`LANES_TIERS`; `get_speed_score`/`get_lanes_score` dropped their `rankings` parameter. `CLASSIFICATION_SCORES` and separation `RANKING` are validated at import against the new `StreetClass` and `SeparationLevel` `Literal` types. Pipeline outputs are unchanged.
- **Routing**: `src/route.py` validates school rows (`Name`, `GlobalID`, `geometry`) and census-block rows (`GEOID20`, `BLKGRP20`, `TRACT20`, `geometry`) through `School`/`CensusBlock` models before routing, raising `ValidationError` on missing columns. `weight` is typed `RouteWeight`. Fixed `compute_routes_from_census_blocks_to_all_schools` returning only the last school's errors; it now returns errors from every school.

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
