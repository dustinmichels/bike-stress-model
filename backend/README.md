# Adv GIS Final Project

Clear notebooks:

```sh
uv run --with jupyter ./clear_notebooks.sh
```

## Data

- OSM data downloaded with OSMnx
- Mass [census blocks](https://open-data-massgis.hub.arcgis.com/datasets/census-2020-blocks/explore)
- [Safe Routes geodabase](https://somervillema-my.sharepoint.com/personal/lworth_somervillema_gov/_layouts/15/onedrive.aspx?id=%2Fpersonal%2Flworth%5Fsomervillema%5Fgov%2FDocuments%2F2025%2D11%2D18%20%2D%20Safe%20Routes%20GIS%20Layers&ga=1)

## Dev

Deploy with render??? and fast API

## Model inputs

- separation_level
- speed_limit
- "busyness"
  - street_classification
  - lane_count

### separation level

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

## More data

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
