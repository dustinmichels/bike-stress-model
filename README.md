# Adv GIS Final Project

Clear notebooks:

```sh
uv run --with jupyter ./clear_notebooks.sh
```

## Dev

Deploy with render??? and fast API

## Map Types

### Cycleway Types

Determining what type of cycleway infrastructure exists on each street segment, requires combining multiple OpenStreetMap tags.

- "cycleway", "cycleway:both", "cycleway:left", "cycleway:right" are all accumulated into a single list.
- If there is "lane" and "cycleway:buffer" or "cycleway:separation", we upgrade the type to "lane_buffered".

### Speed limit

### Traffic level

### Road surface

### Traffic safety

Road safety.

- [Police data](https://data.somervillema.gov/Public-Safety/Police-Data-Crashes/mtik-28va/about_data)

## Next Steps

School safety analysis:

- Look at how safe it is to get to each school by bike.
- Get centroids for each block group, then route from centroid to each school, and summarize the safety of the route.

---

## Tests

```sh
uv run pytest tests/ -v
```

## Data

- [Police Crash data](https://catalog.data.gov/dataset/police-data-crashes)

## Overpass

[OverPass Turbo](https://overpass-turbo.eu/)

```ql
[out:json][timeout:25];

// Fetch the boundary of Somerville, MA
{{geocodeArea:Somerville, Massachusetts}}->.searchArea;

// Get all highway features inside the boundary
(
  way["highway"](area.searchArea);
  relation["highway"](area.searchArea);
);

out body;
>;
out skel qt;
```
