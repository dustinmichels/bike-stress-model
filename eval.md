# Evaluation: OSM data quality (Malden / Everett) and scoring validity

Date: 2026-10-04. Data: cached Overpass responses for the four `PLACES` in `main.py`; MassDOT Bike Inventory 2025 (`Multimodal/BikeInventoryYearEndFiles/FeatureServer/5`) clipped to each city boundary.

## Summary

- **Bike infrastructure tags (60% of the score):** OSM coverage in Malden/Everett is comparable to Somerville. Usable.
- **Street classification (20%):** `highway` is tagged on every edge. Usable.
- **Speed limits (20%):** not usable as-is. `maxspeed` is on 2–5% of roads (Somerville/Cambridge: 81–89%). The 20 mph residential fallback is wrong for both cities; their legal default is 25 mph.
- **Scoring:** the composite formula is correct, but `separation_level.py` has three bugs. Two of them make the Python `composite_score` disagree with the frontend's recomputed score. Several modelling choices bias Malden/Everett specifically.

## 1. OSM data quality

### Tag completeness

Length-weighted (osmnx `length`, meters) over `residential` … `trunk_link`. Raw graphs, before intersection consolidation.

| Metric                           | Somerville | Cambridge | Everett   | Malden   |
| -------------------------------- | ---------- | --------- | --------- | -------- |
| `maxspeed` (all roads)           | 81.0%      | 89.1%     | **5.4%**  | **2.1%** |
| `maxspeed` (tertiary+ arterials) | 80.8%      | 88.0%     | **12.2%** | **5.4%** |
| `lanes` (arterials)              | 97.5%      | 99.5%     | 98.9%     | 99.3%    |
| `width`                          | 91.5%      | 92.1%     | 83.3%     | 88.9%    |
| `surface`                        | 86.8%      | 98.1%     | 41.6%     | 42.9%    |
| any `cycleway*` tag              | 49.7%      | 78.4%     | 17.9%     | 20.2%    |
| `massgis:way_id`                 | 92.4%      | 91.9%     | 77.2%     | 89.6%    |

After the pipeline runs (consolidated graph):

| Metric                               | Somerville | Cambridge | Everett   | Malden    |
| ------------------------------------ | ---------- | --------- | --------- | --------- |
| Network length with no speed         | 32.7%      | 39.4%     | 66.1%     | 60.9%     |
| Arterials with no speed              | 19.2%      | 13.2%     | **87.4%** | **94.2%** |
| Residential set to 20 mph by default | 18.6%      | 6.1%      | **98.4%** | **99.9%** |
| `service` share of network length    | 19.8%      | 19.1%     | 31.8%     | 27.3%     |

Caveat: tags not listed in `ox.settings.useful_tags_way` (e.g. plain `sidewalk`) are dropped by osmnx and would show as 0% regardless of OSM content. None of those are used by the model.

### Bike infrastructure vs. MassDOT Bike Inventory 2025

Share of MassDOT centerline length that lies within 20 m of an OSM edge whose `separation_level` is not `none`. The metric is measured on MassDOT geometry, so OSM's two directed edges per two-way street do not inflate it. Raw OSM-km vs MassDOT-km totals are _not_ comparable for the same reason, so they aren't reported.

| MassDOT type                                              | Somerville    | Cambridge     | Everett       | Malden        |
| --------------------------------------------------------- | ------------- | ------------- | ------------- | ------------- |
| Bike lane                                                 | 96% (17.6 km) | 89% (34.4 km) | 75% (10.6 km) | 92% (8.1 km)  |
| Separated bike lane                                       | 97% (17.8 km) | 95% (29.1 km) | 96% (2.3 km)  | 100% (1.0 km) |
| …tagged as protected (`track`/`separate`/`lane_buffered`) | 92%           | 93%           | 95%           | **51%**       |
| Shared-use path                                           | 72% (11.3 km) | 79% (34.0 km) | 74% (7.1 km)  | 67% (7.4 km)  |

Where the gaps come from:

- **Everett lanes:** Floyd St, Elm St, School St, Charlton St, and parts of Revere Beach Pkwy have no `cycleway*` tags in OSM. This is an OSM data gap, or MassDOT is out of date.
- **Everett paths:** Everett Riverwalk is in OSM as `highway=path` + `bicycle=yes`. It is in the graph but scored `none` (see §2, issue 4). Another ~810 m nearby is `highway=footway` + `bicycle=yes`, which osmnx's `bike` filter excludes.
- **Malden paths:** Fellsmere Park, Spot Pond Brook Greenway, and Pine Banks are absent from OSM's bikeable network; only ~81 m of nearby `footway` + `bicycle=yes` exists. This is an OSM data gap.
- **Pipeline boundary loss:** three Northern Strand Community Trail ways (177 m) are dropped by `ox.graph_from_place` (`main.py:74`). `retain_all=True` alone did not recover them. Adding `truncate_by_edge=True` recovered all three.

### Speed limits

- Malden adopted a 25 mph citywide default ([city of Malden, Nov 2020](https://www.cityofmalden.org/777/Drive-25)). Everett did the same ([NBC Boston](https://www.nbcboston.com/news/local/new-25-mph-speed-limit-takes-effect-in-most-of-everett/2736135/)).
- `speed.py:75-78` sets untagged `residential` to 20 mph. That gives speed score 0 instead of 1 on essentially every residential street in both cities, and leaves them indistinguishable from each other.
- Untagged arterials get no speed component. Their composite falls back to separation + classification, with the weights renormalized.
- Effect on the mean of the frontend-equivalent composite (weighted by the `length` column, meters) if Malden/Everett residential defaulted to 25 mph: Everett 3.06 → 3.12, Malden 3.17 → 3.25. Somerville/Cambridge are unchanged at 2.63/2.45.
- Untagged `service` roads (parking aisles, driveways) get no speed default and score 3.5. `speed.py:75-78` sets untagged `residential` to 20 mph, but ignores `service` (even though `classification.py:19` categorizes it as `residential`). With speed missing (`NaN`), `compute_composite_score` drops the speed term and renormalizes the weights: $(0.60 \times 4.0 + 0.20 \times 2.0) / 0.80 = 3.50$. Missing speed thus acts as an unintended penalty, scoring low-speed parking aisles and alleys worse than a 20 mph residential street (2.80) or 25 mph residential street (3.00). Because untagged `service` roads represent a much larger share of the network in Malden/Everett (27–32% of length, 28–31% of edges vs. ~19–20% in Somerville/Cambridge; >99.8% untagged for speed), this missing-data penalty raises those cities' aggregate stress.

Ground truth for arterial speeds would come from the MassDOT Road Inventory, which has posted speed for all roads. The Bike Inventory's speed field only covers bike-facility segments. This comparison was not run.

### Verdict

OSM is adequate for separation and classification in Malden/Everett, but not for speed. Fix the speed default per city before comparing Malden/Everett against Somerville/Cambridge, and consider filling arterial speeds from the MassDOT Road Inventory.

## 2. Scoring validity

The composite formula is correct in both implementations. `compute_composite_score` (`main.py`) and `calculateCompositeScore` (`frontend/src/utils/scoreCalculator.ts`) both take a weighted average over non-null factors. Python and frontend speed bands match. Divergence comes only from the inputs below.

### Bugs

1. **Unknown cycleway values score 0 (best).** `separation_level.py:48` (`pick_best`) and `:135` both use `RANKING.get(v, 0)`.
   - Observed unknown values: `shoulder`, `crossing`, `ep`, `separation`.
   - Malden's Eastern Ave and Centre St (`primary`, 3.7 km, `cycleway:both=shoulder`) get a Python composite of **0.75**.
   - The frontend treats unknown categories as null, which yields 3.0.
   - Python and the frontend disagree on 3.7 km in Malden, 2.5 km in Cambridge, and 1.4 km in Somerville.
2. **`"no"` inside a list is not normalized.** `separation_level.py:33` only maps scalar `"no"` → `"none"`, but intersection consolidation produces lists. Because of bug 1, `"no"` (score 0) then wins `pick_best`.
   - Example: Cedar St, Somerville: `[shared_lane, lane, no, none, none]` → `no`.
   - Python scores it 0; the frontend aliases it to `none` (4). The correct value is `lane` (2.5).
   - Affected streets: Cedar, Dane, Hancock, and Springfield St in Somerville; Concord Ave, Mount Auburn St, and Prospect St in Cambridge.
3. **`cycleway:separation` fallback is unreachable.** `separation_level.py:53-55` checks `is None`, but a missing `cycleway:buffer` is NaN. The separation tag is therefore never consulted.
   - Example: Grand Union Blvd, Somerville (`cycleway:separation=solid_line`) stays `lane` instead of `lane_buffered`.

### Modelling issues

4. **Shared-use paths without `bicycle=designated` score as unprotected roads.** `separation_level.py:129-131` only marks `highway=cycleway` or `path` + `designated` as `separate`. As a result:
   - `path`/`track` + `bicycle=yes` get separation 4 and a composite of 3.0–3.5. That is worse than a 20 mph residential street (2.8).
   - Everett: Everett Riverwalk (`path` 3.7 km plus `track` 1.1 km, directed). Malden: Fells trails such as Blue Blaze and Pinnacle Path (3.6 km).
   - Unpaved hiking trails in the Fells arguably shouldn't be in a child-cycling network at all; `surface` could gate them.
5. **Equality checks miss list-valued tags.** `separation_level.py:129-130` and `speed.py:75` compare `highway` with `==`. After consolidation, 0.6–0.9% of edges have list-valued `highway`, so the cycleway override and the residential speed default skip them.
   - Example: `['path', 'cycleway']` + `designated` in Cambridge ends up as `crossing`.
6. **List-valued highway takes the most optimistic type.** `classification.py:67` picks the lowest-stress type from merged lists.
7. **`footway` + `bicycle=yes` is excluded** by osmnx's `bike` network filter (~810 m near Everett's MassDOT paths).
8. **The summary mean is unweighted.** `main.py:157` and `:301` average directed edges without length weighting, using the Python composite (affected by bugs 1–2). Two-way streets count twice.
9. **Untagged service roads are penalized by weight renormalization.** `speed.py:75-78` applies the 20 mph default only when `highway == "residential"`, skipping `highway=service`. With no cycleway (separation 4) and residential classification (2), dropping missing speed renormalizes weights to $(0.60 \times 4 + 0.20 \times 2) / 0.80 = 3.5$. Low-speed parking aisles and driveways thus score higher stress than 20 mph residential streets (2.8).

### Minor

- `lanes.run` (`main.py:144`) is computed but never exported or scored.
- The comment in `speed.py` `SPEED_RANKINGS` says `> 50 mph -> 5 points`; the actual score is 4.
- `tests/` has no coverage of `src/stressmodel`. The 18 existing tests cover `util` and `copy_to_frontend` only.

## Recommended fixes (priority order)

1. Treat unknown separation values as missing. Optionally map `shoulder` → `lane` and `crossing` → `none`.
2. Normalize `"no"` → `"none"` inside lists in `combine_cycleways`.
3. Fix the `cycleway:buffer` NaN check so `cycleway:separation` is consulted.
4. Score `path`/`pedestrian` + `bicycle=yes|permissive` as `separate`. Consider gating on `surface`.
5. Make tag checks list-aware (`highway`, `bicycle`).
6. Use a per-city residential speed default (25 mph for Malden/Everett), and set a speed default for `service` roads (or all `residential`-classified types). Consider MassDOT Road Inventory speeds for arterials.
7. Pass `truncate_by_edge=True` to `ox.graph_from_place`.
8. Length-weight the summary mean.
9. Add regression tests for issues 1–5.
