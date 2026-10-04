# Bike Stress Model

A bike stress model and interactive map evaluating cycling infrastructure safety and comfort using OpenStreetMap data. The idea is the evaluate the bike network with children in mind.

The project consists of:

- **Python Stress Model (Root)**: Downloads OSM network data using OSMnx, evaluates street segments across infrastructure factors, and exports GeoJSON / GeoPackage networks.
- **Frontend (`frontend/`)**: Vue 3 + MapLibre web app for interactively exploring street networks with customizable weight sliders.

---

## Setup & Development

Install dependencies with [uv](https://github.com/astral-sh/uv):

```sh
uv sync
```

### Run the Pipeline

Generate network data for configured municipalities:

```sh
uv run main
```

Outputs are written to `data/out/main/`.

### Copy Data to Frontend

Copy generated GeoJSON files into the frontend public data directory (`frontend/public/data`):

```sh
./copy.sh
```

### Run Tests

```sh
uv run pytest tests/ -v
```

### Notebooks

Jupyter notebooks are located in `notebooks/`. To clear notebook output cells before committing:

```sh
uv run --with jupyter ./clear_notebooks.sh
```

---

## Model Inputs

The model evaluates cycling stress across three active components (scored 0 for lowest stress, up to 4 for highest stress):

1. **Separation Level (`src/stressmodel/separation_level.py`)**
   - Assesses cycleway infrastructure type (`separate`, `track`, `lane_buffered`, `lane`, `share_busway`, `shared_lane`, `none`).
   - Identifies buffered lanes via `cycleway:buffer` and `cycleway:separation` tags.

2. **Speed Limit (`src/stressmodel/speed.py`)**
   - Extracts posted speeds, falling back to 20 mph for residential streets when unmapped.
   - Maps speed to stress tiers (≤20 mph: 0, ≤25 mph: 1, ≤30 mph: 2.5, ≤40 mph: 3, ≤50 mph: 3.5, >50 mph: 4).

3. **Street Classification (`src/stressmodel/classification.py`)**
   - Classifies OSM `highway` types into broad categories: `dedicated_path` (0), `residential` (2), `medium-capacity` (3), and `motorway` (4).

A composite score is computed using the weighted average of these factors:

$$\text{Composite Score} = 0.60 \times \text{Separation} + 0.20 \times \text{Speed} + 0.20 \times \text{Classification}$$

---

## Frontend Development

See `frontend/README.md` for instructions on running the frontend:

```sh
cd frontend
bun install
bun run dev
```
