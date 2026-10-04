# TODO: fixes for issues in `eval.md`

Goal: Malden/Everett scores should be comparable with Somerville/Cambridge, and the Python and frontend scores should agree.

## Where each fix has to land

The map does **not** display the Python `composite_score`. `sanitize_for_frontend` strips it (asserted in `tests/test_main.py::test_save_data_for_place`). The frontend recomputes every score from three exported fields:

| Exported field          | Python source          | Frontend lookup                                       |
| ----------------------- | ---------------------- | ----------------------------------------------------- |
| `separation_level`      | `separation_level.run` | `bikeData.ts` categories + `SEPARATION_LEVEL_ALIASES` |
| `street_classification` | `classification.run`   | `bikeData.ts` categories                              |
| `maxspeed_int`          | `speed.run`            | `calculateSpeedScore` bands                           |

So a fix only reaches the map if it changes one of these fields. The Python `composite_score` feeds only the CLI summary table.

**Rule for this plan:** tag interpretation, aliasing and defaults for missing values live in Python only. The frontend just maps an exported category to a score.

Line numbers in `eval.md` for `main.py` are stale. Current ones: `graph_from_place` is at 78, the summary means are at 161/305, and `lanes.run` is at 148.

---

## OSM tag semantics: what the wiki says vs. what the code does

Sources:

- [Key:cycleway](https://wiki.openstreetmap.org/wiki/Key:cycleway)
- [Key:cycleway:separation](https://wiki.openstreetmap.org/wiki/Key:cycleway:separation)
- [Key:cycleway:buffer](https://wiki.openstreetmap.org/wiki/Key:cycleway:buffer)

Counts below are distinct `highway=*` ways in the cached Overpass responses (`cache/*.json`, 19,877 ways). Those responses extend past the four city boundaries, so read the counts as orders of magnitude, not per-city figures.

### `cycleway`, `cycleway:{both,left,right}` values

| Value                                     | Wiki meaning                                                                                                                                                           | Observed                                         | Code today                           | Correct handling                                                                         |
| ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------ | ---------------------------------------------------------------------------------------- |
| `lane`, `shared_lane`, `share_busway`, `track` | As documented                                                                                                                                                     | common                                           | ranked                               | unchanged                                                                                |
| `no`                                      | Road surveyed, **no** bike infrastructure                                                                                                                              | 2,451                                            | scalar → `none`; inside a list → 0 (**best**) | `none`, also inside lists                                                       |
| **`separate`**                            | The bike facility is **mapped as its own way** (`highway=cycleway`). The road itself carries none.                                                                     | **325 road ways**, mostly primary/secondary/trunk | `separate` = 0 (**best**)            | **`none` for the road edge**: the parallel `highway=cycleway` edge carries the protection |
| `shoulder`                                | "**No designated infrastructure for cyclists**", but a rideable shoulder                                                                                               | 14 (Eastern Ave, Centre St in Malden)            | unknown → 0 (**best**)               | `none`. See decision D1                                                                  |
| `crossing`, `traffic_island`, `link`, `construction` | Homonymous use: these describe a **`highway=cycleway`** way itself (e.g. its crossing segment), not on-road infrastructure                                 | 335, **all on `highway=cycleway`**               | unknown → 0                          | Ignore `cycleway*` on dedicated-path highways. Separation comes from `highway`/`bicycle` |
| `separation`                              | **Not a documented value.** One way: Foley St, `cycleway:right=separation` + `cycleway:both=track`. Probably a mis-tag for the `cycleway:separation` key.            | 1                                                | unknown → 0; frontend aliases it to `separate` | **Drop** as unknown. Delete the frontend alias                                 |
| `ep`                                      | Not documented. Powder House Blvd `cycleway:left=ep` is a typo.                                                                                                        | 1                                                | unknown → 0                          | Drop as unknown                                                                          |
| `shared`                                  | Deprecated; it was for `highway=cycleway`. Here it's on a residential road (Longfellow Rd).                                                                            | 1                                                | unknown → 0                          | Drop as unknown                                                                          |
| `opposite*`                               | Deprecated                                                                                                                                                             | 0                                                | —                                    | No handling needed                                                                       |

The `separate` row is the biggest semantic error. eval.md did not catch it. Its MassDOT "…tagged as protected (`track`/`separate`/`lane_buffered`)" row counts road ways tagged `separate` as protected, so that row has to be re-measured.

### `cycleway:separation` / `cycleway:buffer`

- **`cycleway:separation`** describes *physical* separation. Documented values: `no`, `bollard`, `flex_post`, `vertical_panel`, `bump`, `planter`, `kerb`, `greenery`, `hedge`, `tree_row`.
  - Observed but undocumented: `parking_lane` (3), `yes` (8), `solid_line` (1).
  - A solid painted line is not physical separation. That means eval.md bug 3's expected outcome is wrong: Grand Union Blvd (`solid_line`) should stay `lane`, not become `lane_buffered`. The bug is still real (the NaN check means the key is never read); only the expected result changes.
- **`cycleway:buffer`** is "the amount of space between the cycleway and the car lanes". Values: `yes`, `no`, or a width. The code's conflation (buffer *or* separation → `lane_buffered`) treats space and physical barriers as one thing.
- **Side-specific variants are silently dropped.** `cycleway:{left,right,both}:separation` and `:buffer` aren't in `ox.settings.useful_tags_way` (`main.py:30-48`), so osmnx discards them. Observed:
  - `cycleway:right:separation=flex_post`: 269 ways
  - `cycleway:left:separation=flex_post`: 88 ways
  - `cycleway:right:buffer=yes`: 162 ways

  The unsided keys the model reads are an order of magnitude rarer (≈45 values each). eval.md missed this.

### Direction

`cycleway:right` applies to the way's forward direction and `cycleway:left` to its backward direction (right-hand traffic). osmnx builds a separate directed edge for each direction, but `combine_cycleways` takes the best of *all* sides for *both* edges. 432 two-way ways have different left/right values. Example: Centre St, Malden (`right=shoulder`, `left=no`). In these cases one direction gets credit for infrastructure that is only on the other side.

---

## P0: fix before comparing cities

### 1. Canonicalize separation values per the wiki (eval bugs 1, 2; tag table above)

**Fix** in `src/stressmodel/separation_level.py`:

- **Dedicated-path highways** (`cycleway`, `path`, `pedestrian`, `footway`, `track`, `bridleway`): ignore every `cycleway*` value. Separation is decided by P0 item 5 alone. This removes `crossing`/`traffic_island`/`link`/`construction` from the problem.
- **Roads:** flatten lists/ndarrays, then map each element:
  ```python
  ROAD_ALIASES = {"no": "none", "separate": "none", "shoulder": "none"}
  ```
  - Drop anything not in `RANKING` after aliasing (`separation`, `ep`, `shared`, future junk). Count dropped values with a `Counter` and log them once per run.
  - Missing columns still contribute `"none"`, so **separation is never null**. An edge with only unknown values resolves to `none` (4). This is deliberate: an unknown value means no evidence of infrastructure, so the edge is scored as having none instead of letting the weight renormalization decide.
- Remove `separate` from what road edges can emit. The `separate` category stays, but only P0 item 5 sets it.
- `pick_best` → `min(values, key=RANKING.__getitem__)`. Score lookup → `RANKING[level]`. A `KeyError` means the invariant broke.
- Delete `SEPARATION_LEVEL_ALIASES` in `frontend/src/utils/scoreCalculator.ts` (its `separation → separate` entry is wrong per the wiki). Keep `warnOnce`.

**Verify before merging:** for every road edge tagged `separate`, check that a `separation_level=separate` edge exists within ~20 m. Where none exists, the parallel facility is missing from the graph, usually because it is a `footway` (P1 item 2). Report those km.

### 2. Separation/buffer: read all sides, interpret by meaning (eval bug 3 + side keys)

- Add to `useful_tags_way`:
  - `cycleway:{both,left,right}:separation`
  - `cycleway:{both,left,right}:buffer`
  - `cycleway:{left,right}:oneway` (needed by P1 item 6)
- Replace `apply_buffer_to_list` and `adjust_track_with_separation` with one function that resolves each side as (base value, buffer, separation). Use the side-specific key first, then `:both`, then unsided. Use the NaN-safe, list-aware helpers from P0 item 3. Split `cycleway:separation` on `;`, since the wiki allows multiple values.
- Upgrade rules:

  | Base    | Condition                                                             | Result          |
  | ------- | --------------------------------------------------------------------- | --------------- |
  | `lane`  | buffer ∉ {missing, `no`, `0`}                                         | `lane_buffered` |
  | `lane`  | separation ∈ {`flex_post`, `vertical_panel`, `bump`, `yes`}           | `lane_buffered` |
  | `lane`  | separation ∈ {`kerb`, `bollard`, `planter`, `hedge`, `greenery`, `tree_row`} | `track` (wiki: physically separated lanes "are usually understood as cycle track") |
  | `track` | separation ∈ {`flex_post`, `vertical_panel`, `bump`}                  | `lane_buffered` (existing model choice: wiki says flex posts are something "a car could run over") |
  | any     | separation ∈ {`no`, `solid_line`, `dashed_line`}                      | unchanged       |

- `parking_lane`: see decision D2.

### 3. List-aware tag checks (eval issue 5)

**Problem.** `highway == "cycleway"`, `bicycle == "designated"` (`separation_level.py:129-130`) and `highway == "residential"` (`speed.py:75`) are False for list-valued tags. That covers 0.6–0.9% of edges after consolidation.

**Fix:**

- New `src/stressmodel/tags.py` with:
  - `as_list(v) -> list[str]` (scalar/list/ndarray/NaN)
  - `present(v) -> bool` (False for None/NaN/`"no"`; list-aware)
  - `has_any(series, values) -> pd.Series[bool]`
- Use these at every tag check in `separation_level.py` and `speed.py`. One convention, no per-module variants.

### 4. Speed defaults per city, for every residential-class road (eval speed section + issue 9)

**Problems (three):**

- **Wrong residential default.** Untagged `residential` streets get 20 mph everywhere. Malden and Everett adopted 25 mph ([Malden](https://www.cityofmalden.org/777/Drive-25), [Everett](https://www.nbcboston.com/news/local/new-25-mph-speed-limit-takes-effect-in-most-of-everett/2736135/)). Somerville and Cambridge use 20 mph on most residential streets ([Somerville](https://www.somervillema.gov/content/somerville-speed-limits-and-safety-zones), [Cambridge](https://www.cambridgema.gov/streetsandtransportation/policiesordinancesandplans/visionzero/speedlimitsincambridge)).
- **Service roads skipped.** Untagged `service` gets no default, even though classification puts it in `residential`. Renormalizing over the missing speed gives 3.5, worse than a 20 mph street (2.8). This hits 27–32% of network length in Malden/Everett.
- **Arterials penalized.** eval.md:61 notes that untagged arterials are renormalized, but not which way this pushes the score. With no bike facility on a `medium-capacity` road:
  - Missing speed: $(0.6 \cdot 4 + 0.2 \cdot 3)/0.8 = 3.75$
  - With a posted speed: $3.2$ at 25 mph, $3.5$ at 30, $3.6$ at 40, $3.7$ at 50.

  So an untagged arterial scores worse than a tagged 50 mph one. 87–94% of Malden/Everett arterials are untagged. [INFERENCE from the formula; size not measured. See P1 item 5.]

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
  `main()` iterates `.items()`; `copy_to_frontend(places=list(PLACES))` keeps its `list[str]` signature.
- In `prepare_data_for_place`, run `classification.run` before `speed.run`. Pass the classification Series and the city default into `speed.run(df, residential_default_mph, street_classification)`.
- Apply the default where `maxspeed_int` is NaN **and** `street_classification == "residential"`. That covers `residential`, `living_street`, `service`, `unclassified`, `track`, and also list-valued `highway`.
- Delete `DEFAULT_SPEED_LIMIT` (always `None`, dead config). Delete the `defaultCategory` fields in `bikeData.ts`/`types.ts`. `types.ts:17` documents them as "Default category to use when data is missing", but `scoreCalculator.ts` never reads them; the speed one claims a 25 mph default that is never applied. Python is the only place defaults are applied.
- Arterials: leave them NaN here. Fix them with data (P1 item 5), not a guessed default.

**Expected effect:** untagged service roads in Everett/Malden go from 3.5 to 3.0, and residential streets from 2.8 to 3.0.

### 5. Score shared-use paths as `separate` (eval issue 4)

**Problem.** `separate` requires `highway=cycleway`, or `path` + `bicycle=designated`. Everett Riverwalk (`path`/`track` + `bicycle=yes`) scores 3.0–3.5, worse than a residential street. On paths, `bicycle=yes` means cycling is legal and `designated` means it is signed. Either way the path is separated from motor traffic, which is what this factor measures.

**Fix** in `separation_level.run`, using `has_any`:

```python
SHARED_USE = {"path", "pedestrian", "footway"}
BIKE_OK = {"designated", "yes", "permissive"}
UNPAVED = {"dirt", "earth", "ground", "grass", "mud", "sand", "rock", "woodchips", "unpaved"}
is_separate = has_any(hw, {"cycleway"}) | (
    has_any(hw, SHARED_USE) & has_any(bicycle, BIKE_OK) & ~has_any(surface, UNPAVED)
)
```

- Missing `surface` (57–58% of ways in Malden/Everett) passes the gate. Excluding everything without a surface tag would drop real paths.
- `highway=track` is **not** included. Per the wiki it is a road "for mostly agricultural or forestry uses" and does not exclude motor vehicles by itself. Include a `track` only when `motor_vehicle`/`access` excludes general traffic. That needs `motor_vehicle` added to `useful_tags_way`. Check the Riverwalk's `track` ways against this rule before deciding they qualify.

---

## P1: correctness of inputs and summary

### 1. Recover boundary-straddling ways

In `get_network`: `ox.graph_from_place(place, network_type=network_type, truncate_by_edge=True)`. eval.md says this recovers the three Northern Strand ways (177 m). Verified that osmnx 2.1.1 supports the parameter.

### 2. Include `footway` + `bicycle=yes` (eval issue 7)

The osmnx `bike` filter excludes `highway=footway` outright (`osmnx/_overpass.py:112-118`). Download a second graph and compose it before projection. Keep the bike filter's area, access and service exclusions:

```python
G_foot = ox.graph_from_place(
    place,
    network_type="bike",
    truncate_by_edge=True,
    custom_filter=(
        f'["highway"="footway"]["area"!~"yes"]{ox.settings.default_access}'
        '["footway"!~"sidewalk|crossing"]["service"!~"private"]'
        '["bicycle"~"^(yes|designated|permissive)$"]'
    ),
)
G = nx.compose(G, G_foot)
```

This excludes sidewalks and crossings, so `bicycle=yes` sidewalks don't become "paths". With P0 item 5, these edges score `separate`. This also closes gaps found by the P0 item 1 check (roads tagged `separate` whose parallel facility is a footway).

### 3. List-valued `highway` → most stressful type (eval issue 6)

In `classification.extract_street_type`, change `min` to `max`. This makes it consistent with `extract_maxspeed`, which already takes the max of a list.

### 4. Length-weighted summary (eval issue 8)

- Add a helper in `main.py` that returns the length-weighted mean and median of `composite_score` over non-null rows. Use it at both call sites (`main.py:161`, `:305`).
- Keep both directed edges. After P1 item 6 the two directions of a street legitimately differ, so the metric is "per direction-km". Label the table that way.

### 5. Arterial speeds from the MassDOT Road Inventory

1. **Measure first:** compute the Malden/Everett mean with untagged arterials at NaN vs. at 30 mph.
2. Join the Road Inventory posted speed to OSM edges that lack `maxspeed`. Match within ~15 m of centerline, with bearing agreement, on tertiary-and-above edges only. Keep OSM `maxspeed` where it exists.
3. Cache the inventory download like the Overpass cache.

### 6. Side-aware separation per directed edge

- Forward edge (osmnx `reversed=False`): `cycleway:right` + `:both` + unsided. Reverse edge: `cycleway:left` + `:both` + unsided.
- One-way roads have only a forward edge. Both sides apply to it, except a side whose `cycleway:<side>:oneway=-1` (contraflow). A side with `cycleway:<side>:oneway=no` (two-way track) applies to both edges.
- `reversed` can be list-valued after consolidation. Use `as_list`.
- **Frontend consequence:** both directed edges are drawn on the same line. Once they differ, the map shows whichever renders last. Either export one feature per street with the worse direction's category, or offset the two directions. Decide this before implementing (decision D3).

### 7. Regression tests

Add `tests/test_stressmodel.py` with small hand-built DataFrames:

- Road values:
  - `cycleway:right=separate` (no other tags) → `none`
  - `cycleway:both=shoulder` → `none`
  - `cycleway:right=separation` + `cycleway:both=track` → `track`
  - `cycleway=ep` alone → `none`
  - `[shared_lane, lane, no, none]` → `lane`
  - every emitted `separation_level` ∈ `RANKING`
- `highway=cycleway` + `cycleway=crossing` → `separate`.
- Separation/buffer:
  - `lane` + NaN `cycleway:buffer` + `cycleway:separation=solid_line` → `lane`
  - `lane` + `cycleway:right:buffer=yes` → `lane_buffered`
  - `lane` + `cycleway:right:separation=kerb` → `track`
  - `track` + `cycleway:right:separation=flex_post` → `lane_buffered`
- Paths:
  - `path` + `bicycle=yes` + missing surface → `separate`
  - `path` + `bicycle=yes` + `surface=ground` → not `separate`
  - `['path', 'cycleway']` → `separate`
  - `track` + `bicycle=yes` without a motor-vehicle exclusion → not `separate`
- Direction: `right=lane`, `left=no`, two-way → forward edge `lane`, reverse edge `none`.
- Speed:
  - untagged `service`, default 25 → 25
  - untagged `primary` → NaN
  - tagged `residential` 30 → 30
- Classification: `['residential', 'primary']` → `medium-capacity`.
- Summary helper: longer edges weigh more.

---

## P2: minor

- Fix the `speed.py` `SPEED_RANKINGS` comment: `> 50 mph -> 4 points`.
- Category scores are duplicated in Python `RANKING` and `bikeData.ts`. Move the default scores to one JSON file (e.g. `frontend/src/data/scores.json`) that `bikeData.ts` imports and Python loads. The frontend's runtime score overrides keep working on top of it.
- `lanes`: eval.md says it is "never exported". That's wrong: `lanes_int` is in `OUTPUT_COLUMNS` and in the shipped GeoJSON. It is computed and exported but not scored. Leave it as is.
- `cycleway:*:lane=advisory` (14 ways) marks lanes motorists may enter. Leave it scored as `lane` unless advisory lanes become common.

## Decisions needed

- **D1 — `shoulder`:** `none` (default; wiki: "no designated infrastructure"), or a new `shoulder` category (e.g. 3.5) that gives partial credit for space outside the travel lane. Before deciding, check Eastern Ave/Centre St against MassDOT and imagery. If MassDOT lists bike lanes there, the OSM tag is the error and should be fixed upstream.
- **D2 — `cycleway:separation=parking_lane` on `track`:** the current code downgrades it to `lane_buffered`. The wiki says US practice tags parking-protected lanes as `track`. Default: stop downgrading (keep `track`).
- **D3 — map rendering of the two directions** (P1 item 6): worst-of-both per street (default, simpler) or offset lines.
- **D4 — unpaved Fells trails:** keep them scored `none`/`dedicated_path` (3.0, default), or drop unpaved `path`/`track` from the exported network.

## Done when

- Rerunning the eval.md measurements gives:
  - **0 km** of Python-vs-frontend composite disagreement in all four cities.
  - Spot checks:
    - Eastern Ave/Centre St (Malden) → the D1 choice
    - Cedar St (Somerville) → `lane`
    - Grand Union Blvd → `lane` (`solid_line` is not separation)
    - Foley St → `track`
    - Everett Riverwalk `path` ways → `separate`
    - Northern Strand ways present
  - The MassDOT "tagged as protected" row is re-measured without counting road ways tagged `separate`.
  - Every road edge tagged `separate` has a `separate` edge within 20 m, or appears in a list of exceptions.
  - Residential-class edges with a defaulted speed carry 25 in Malden/Everett and 20 in Somerville/Cambridge.
- Per-city length-weighted means are recorded before and after each P0 item, so the size of each fix is visible.
- Frontend: load each city, confirm no `Unknown separation_level category` warnings in the console, and spot-check the streets above in their popups.
- `CHANGELOG.md` entry; `README.md` documents the per-city speed defaults and the tag-interpretation table.
