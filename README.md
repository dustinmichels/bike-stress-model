# Adv GIS Final Project

Clear notebooks:

```sh
uv run --with jupyter ./clear_notebooks.sh
```

### Tests

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
