# TODO: fixes for issues in `eval.md`

Goal: Malden/Everett scores should be comparable with Somerville/Cambridge, and the Python and frontend scores should agree.

## Where each fix has to land

The map does **not** display the Python `composite_score`. `sanitize_for_frontend` strips it (asserted in `tests/test_main.py::test_save_data_for_place`). The frontend recomputes every score from three exported strings/numbers:

| Exported field          | Python source          | Frontend lookup                                       |
| ----------------------- | ---------------------- | ----------------------------------------------------- |
| `separation_level`      | `separation_level.run` | `bikeData.ts` categories + `SEPARATION_LEVEL_ALIASES` |
| `street_classification` | `classification.run`   | `bikeData.ts` categories                              |
| `maxspeed_int`          | `speed.run`            | `calculateSpeedScore` bands                           |

So a fix only reaches the map if it changes one of these fields. The Python `composite_score` feeds only the CLI summary table.

Line numbers in `eval.md` for `main.py` are stale. Current ones: `graph_from_place` is at 78, the summary means are at 161/305, and `lanes.run` is at 148.

---

## P0: fix before comparing cities

### 1. Canonicalize separation values (eval bugs 1, 2)

**Problem.** Unknown cycleway values (`shoulder`, `crossing`, `ep`, `separation`) get `RANKING.get(v, 0)`, which is the _best_ score. `"no"` is only normalized when it's a scalar, so `"no"` inside a list wins `pick_best`. Effects:

- Python emits non-canonical strings.
- The frontend nulls them (`shoulder` → 3.0 on Eastern Ave/Centre St) or aliases them (`no` → `none` = 4 on Cedar St, where `lane` = 2.5 is correct).

**Fix** in `src/stressmodel/separation_level.py`:

- Add one alias table and apply it per element, after flattening lists and ndarrays:
  ```python
  ALIASES = {
      "no": "none",
      "separation": "separate",
      "crossing": "none",
      "shoulder": "lane",
  }
  ```
- Drop values that are still unknown after aliasing. Count them with a `Counter` and log once per run so new tag values show up. Each tag column that is missing still contributes `"none"`, so an edge whose only values are unknown resolves to `none`.
- `pick_best` → `min(values, key=RANKING.__getitem__)`. The score lookup becomes `RANKING[level]`. A `KeyError` there means the invariant broke, and it should fail loudly instead of scoring 0.
- Delete `SEPARATION_LEVEL_ALIASES` from `frontend/src/utils/scoreCalculator.ts`, because Python now emits canonical values only. Keep `warnOnce` for unknown categories.

**Decision needed:** `shoulder` → `lane` follows eval.md. The conservative alternative is `shared_lane` (3.5): a paved shoulder isn't a designated bike facility, and Eastern Ave is a 4-lane primary road. Default is `lane` unless overruled.

### 2. Make `cycleway:separation` reachable (eval bug 3)

**Problem.** `apply_buffer_to_list` falls back to `cycleway:separation` only when `cycleway:buffer is None`. A missing column value is NaN, so the fallback never runs. Example: Grand Union Blvd stays `lane`.

**Fix:**

- Add a `_present(v)` helper. It returns False for None/NaN/`"no"` and is list-aware (any element present).
- Use it for both the buffer check and the fallback.
- `adjust_track_with_separation` has the same list blind spot: `separation in ["flex_post", "parking_lane"]` fails on a list-valued tag. Route it through the same helper.

### 3. List-aware tag checks (eval issue 5)

**Problem.** `highway == "cycleway"`, `bicycle == "designated"` (`separation_level.py:129-130`) and `highway == "residential"` (`speed.py:75`) are False for list-valued tags. That covers 0.6–0.9% of edges after consolidation.

**Fix:**

- New `src/stressmodel/tags.py` with:
  - `as_list(v) -> list[str]` (scalar/list/ndarray/NaN)
  - `has_any(series, values) -> pd.Series[bool]`
- Use it at every tag equality check in `separation_level.py` and `speed.py`, and in fix 2's helper. One convention, no per-module variants.

### 4. Speed defaults per city, for every residential-class road (eval speed section + issue 9)

**Problems (three):**

- **Wrong residential default.** Untagged `residential` streets get 20 mph everywhere. Malden and Everett adopted 25 mph ([Malden](https://www.cityofmalden.org/777/Drive-25), [Everett](https://www.nbcboston.com/news/local/new-25-mph-speed-limit-takes-effect-in-most-of-everett/2736135/)). Somerville and Cambridge use 20 mph on most residential streets ([Somerville](https://www.somervillema.gov/content/somerville-speed-limits-and-safety-zones), [Cambridge](https://www.cambridgema.gov/streetsandtransportation/policiesordinancesandplans/visionzero/speedlimitsincambridge)).
- **Service roads skipped.** Untagged `service` gets no default, even though classification puts it in `residential`. Renormalizing over the missing speed gives 3.5, worse than a 20 mph street (2.8). This hits 27–32% of network length in Malden/Everett.
- **Arterials penalized.** Missing speed also inflates untagged arterials, which is not covered in eval.md. With no bike facility on a `medium-capacity` road:
  - Missing speed: $(0.6 \cdot 4 + 0.2 \cdot 3)/0.8 = 3.75$
  - With a posted speed: $3.2$ at 25 mph, $3.5$ at 30, $3.6$ at 40, $3.7$ at 50.

  So an untagged arterial scores worse than a tagged 50 mph one. 87–94% of Malden/Everett arterials are untagged. That makes this a city-level bias, not just noise. [INFERENCE from the formula; size not measured. See P1 item 5.]

**Fix:**

- `main.py`: turn `PLACES` into a mapping from place to residential default mph:
  ```python
  PLACES = {
      "Somerville, Massachusetts, USA": 20,
      "Cambridge, Massachusetts, USA": 20,
      "Everett, Massachusetts, USA": 25,
      "Malden, Massachusetts, USA": 25,
  }
  ```
  Update both consumers: `main()` iterates `.items()`, and `copy_to_frontend(places=list(PLACES))` keeps its `list[str]` signature.
- In `prepare_data_for_place`, run `classification.run` before `speed.run`. Pass the classification Series and the city default into `speed.run(df, residential_default_mph, street_classification)`.
- Apply the default where `maxspeed_int` is NaN **and** `street_classification == "residential"`. That covers `residential`, `living_street`, `service`, `unclassified`, `track`, and also fixes list-valued `highway`.
- Delete `DEFAULT_SPEED_LIMIT` (always `None`, dead config). Delete the unused `defaultCategory` fields in `bikeData.ts`/`types.ts`: the speed one claims a 25 mph default that is never applied. Python owns defaults.
- Arterials: leave them NaN here. Fix them with data in P1 item 5, not with a guessed default.

**Expected effect:** untagged service roads in Everett/Malden go from 3.5 to 3.0, and residential streets from 2.8 to 3.0.

### 5. Score shared-use paths as `separate` (eval issue 4)

**Problem.** `separate` requires `highway=cycleway`, or `path` + `bicycle=designated`. Everett Riverwalk (`path`/`track` + `bicycle=yes`) scores 3.0–3.5, worse than a residential street.

**Fix** in `separation_level.run`, using `has_any` from fix 3:

```python
SHARED_USE = {"path", "pedestrian", "footway", "track"}
BIKE_OK = {"designated", "yes", "permissive"}
UNPAVED = {
    "dirt",
    "earth",
    "ground",
    "grass",
    "mud",
    "sand",
    "rock",
    "woodchips",
    "unpaved",
}
is_separate = has_any(hw, {"cycleway"}) | (
    has_any(hw, SHARED_USE) & has_any(bicycle, BIKE_OK) & ~has_any(surface, UNPAVED)
)
```

Missing `surface` (57–58% of ways in Malden/Everett) passes the gate. Excluding everything without a surface tag would drop real paths.

**Decision needed:** what to do with unpaved Fells trails (Blue Blaze, Pinnacle Path). With the gate above they stay `none`/`dedicated_path` and score 3.0. The alternative is to drop unpaved `path`/`track` from the exported network as not child-rideable. That changes network length and the summary. Default is to keep them scored `none` unless overruled.

---

## P1: correctness of inputs and summary

### 1. Recover boundary-straddling ways

In `get_network`: `ox.graph_from_place(place, network_type=network_type, truncate_by_edge=True)`. eval.md says this recovers the three Northern Strand ways (177 m). Verified that osmnx 2.1.1 supports the parameter.

### 2. Include `footway` + `bicycle=yes` (eval issue 7)

The osmnx `bike` filter excludes `highway=footway` outright (`osmnx/_overpass.py:112-118`). Don't copy that private filter string. Instead, download a second graph and compose it before projection:

```python
G_foot = ox.graph_from_place(
    place,
    network_type="bike",
    truncate_by_edge=True,
    custom_filter='["highway"="footway"]["footway"!~"sidewalk|crossing"]["bicycle"~"^(yes|designated|permissive)$"]',
)
G = nx.compose(G, G_foot)
```

This excludes sidewalks and crossings, so `bicycle=yes` sidewalks don't become "paths". With P0 item 5, these edges score `separate`. eval.md counts about 810 m near Everett's MassDOT paths and 81 m in Malden.

### 3. List-valued `highway` → most stressful type (eval issue 6)

In `classification.extract_street_type`, change `min` to `max`. This makes it consistent with `extract_maxspeed`, which already takes the max of a list. A consolidated `['residential', 'primary']` edge should not score as residential.

### 4. Length-weighted, de-duplicated summary (eval issue 8)

- Add a helper in `main.py`:
  - Drop the reverse twin of each directed pair (`(v, u, k)` when `(u, v, k)` exists). After P0 item 1, both directions carry identical attributes, because `combine_cycleways` merges both sides.
  - Return the length-weighted mean and median of `composite_score` over non-null rows.
- Use it at both call sites (`main.py:161`, `:305`).
- After P0 items 1–2, the Python composite matches the frontend's. The summary then describes what the map shows.

### 5. Arterial speeds from the MassDOT Road Inventory

This is the only real fix for the arterial bias in P0 item 4. Steps:

1. **Measure first:** compute the Malden/Everett mean with untagged arterials at NaN vs. at 30 mph. That gives an upper bound on the bias.
2. Join the Road Inventory posted speed to OSM edges that lack `maxspeed`. Match within about 15 m of centerline, with bearing agreement, on tertiary-and-above edges only. Keep OSM `maxspeed` where it exists.
3. Cache the inventory download like the Overpass cache.

### 6. Regression tests (eval "Minor", fix 9)

Add `tests/test_stressmodel.py` with small hand-built DataFrames that pin behavior, not wiring:

- Separation:
  - `cycleway:both=shoulder` → `lane`
  - `cycleway=ep` alone → `none`
  - `[shared_lane, lane, no, none]` → `lane`
  - every emitted `separation_level` ∈ `RANKING`
- `cycleway:buffer` NaN + `cycleway:separation=solid_line` → `lane_buffered`. List-valued `cycleway:separation=[flex_post, …]` on a `track` → `lane_buffered`.
- Paths:
  - `path` + `bicycle=yes` + missing surface → `separate`
  - `path` + `bicycle=yes` + `surface=ground` → not `separate`
  - `['path', 'cycleway']` → `separate`
- Speed:
  - untagged `service` with default 25 → 25
  - untagged `primary` → NaN
  - tagged `residential` 30 → 30 (the tag beats the default)
- Classification: `['residential', 'primary']` → `medium-capacity`.
- Summary helper: a two-way pair counts once, and longer edges weigh more.

---

## P2: minor

- Fix the `speed.py` `SPEED_RANKINGS` comment: `> 50 mph -> 4 points`.
- `lanes`: eval.md says it is "never exported". That's wrong: `lanes_0`/`lanes_int`/`lanes_int_score` are in `OUTPUT_COLUMNS`, and `lanes_int` appears in the shipped GeoJSON. It is computed and exported but never scored. Leave it as is unless lanes become a scoring factor. Removing it would change the frontend data contract for no gain.

## Done when

- Rerunning the eval.md measurements gives:
  - **0 km** of Python-vs-frontend composite disagreement in all four cities.
  - Spot checks:
    - Eastern Ave/Centre St (Malden) → the chosen `shoulder` mapping
    - Cedar St (Somerville) → `lane`
    - Grand Union Blvd → `lane_buffered`
    - Everett Riverwalk → `separate`
    - Northern Strand ways present
  - Residential-class edges with a defaulted speed carry 25 in Malden/Everett and 20 in Somerville/Cambridge.
- Per-city length-weighted means are recorded before and after, so the size of each fix is visible.
- Frontend: load each city, confirm no `Unknown separation_level category` warnings in the console, and spot-check the streets above in their popups.
- `CHANGELOG.md` entry; `README.md` documents the per-city speed defaults and their sources.
