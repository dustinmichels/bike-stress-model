import collections
import os
import re

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

FEET_TO_M = 0.3048

SpeedInput = str | float | list[str]


def extract_width(value) -> float:
    """
    Width could be in meters (default) or feet (using notation like 9' or 9'6").
    It could also be a list of widths; in that case, return the maximum width.

    Return numeric width in meters from OSM width tags.
    """

    # Handle list - get maximum width
    if isinstance(value, list):
        widths = []
        for item in value:
            width = _parse_single_width(item)
            if not np.isnan(width):
                widths.append(width)
        return max(widths) if widths else np.nan

    # Handle NaN/None
    if pd.isna(value):
        return np.nan

    # Handle single value
    return _parse_single_width(value)


def _parse_single_width(value):
    """Parse a single width value (helper function)."""
    if pd.isna(value):
        return np.nan

    # Convert to string and strip whitespace
    s = str(value).strip()

    # Feet notation like 9' or 9'6"
    if "'" in s:
        # Match feet and optional inches: 9'6" or just 9'
        match = re.match(r"(\d+(?:\.\d+)?)'(?:\s*(\d+(?:\.\d+)?)\")?", s)
        if match:
            feet = float(match.group(1))
            inches = float(match.group(2)) if match.group(2) else 0
            return (feet + inches / 12.0) * FEET_TO_M
        else:
            # Fallback: just extract the number before the '
            match = re.search(r"(\d+(?:\.\d+)?)", s)
            if match:
                return float(match.group()) * FEET_TO_M
            return np.nan

    # Standard numeric meters
    match = re.search(r"\d+(?:\.\d+)?", s)
    if match:
        return float(match.group())

    return np.nan


def first_if_list(series: pd.Series) -> pd.Series:
    """
    Converts any list in a pandas Series to its first element,
    leaves other values unchanged.

    Parameters
    ----------
    series : pd.Series
        The pandas Series to process.

    Returns
    -------
    pd.Series
        Series with lists replaced by their first element.


    Usage
    -----
    >>> edges['cycleway'] = first_if_list(edges['cycleway'])
    """
    return series.apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x)


# Properties required by the frontend web map (scoreCalculator.ts, tooltipUtils.ts, Map.vue).
# All other properties (such as precalculated model scores, raw graph attributes, and intermediate widths)
# are stripped to minimize payload size and improve parsing performance.
FRONTEND_PROPERTIES: list[str] = [
    "name",
    "separation_level",
    "street_classification",
    "maxspeed_int",
    "lanes_int",
]


def sanitize_for_frontend(
    edges: gpd.GeoDataFrame,
    out_path: str | None = None,
    precision: int = 6,
    dedup_reciprocal: bool = True,
    columns: list[str] | None = None,
) -> gpd.GeoDataFrame:
    """
    Sanitize and compact a street network GeoDataFrame for the frontend web application.

    Optimizations performed:
    -----------------------
    1. Attribute pruning:
       - Retains only the columns needed by the frontend: 'name', 'separation_level',
         'street_classification', 'maxspeed_int', and 'lanes_int'.
       - Strips precomputed scores ('composite_score', 'separation_level_score', etc.)
         because useBikeModel.ts recalculates them dynamically on the client based on slider values.
       - Strips unused debug and intermediate attributes ('length', 'width_float', 'width_half',
         'street_0', 'maxspeed_0') and graph routing IDs ('u', 'v', 'key'), since the frontend
         generates its own contiguous '__id' index for interactive feature selection.
    2. Value unpacking & cleaning:
       - Flattens list or ndarray values (such as multi-name arrays produced by OSMnx)
         into single scalar strings.
       - Replaces missing values (NaN / None) cleanly so they serialize to compact JSON nulls.
    3. Duplicate reciprocal edge deduplication:
       - OSMnx directed graphs store both forward (u -> v) and backward (v -> u) edges for two-way streets.
       - When dedup_reciprocal=True, reciprocal twins with identical stress model attributes
         are deduplicated, keeping only one direction. This removes ~25-30% of redundant features
         and vertices without altering visual rendering or click behavior.
       - If attributes differ between directions (e.g. an asymmetric cycle track on one side),
         both directions are preserved.
    4. Coordinate precision reduction:
       - Snaps vertex coordinates to the specified decimal precision (default: 6 decimal places,
         corresponding to ~0.1m ground accuracy).
       - Eliminates sub-nanometer float64 reprojection artifacts and collapses redundant micro-segments.
    5. Minified export:
       - If out_path is supplied, serializes to compact GeoJSON without formatting whitespace
         or deprecated CRS blocks, and writes the output file.

    Parameters
    ----------
    edges : gpd.GeoDataFrame
        Input street network GeoDataFrame (with geometry and attributes).
    out_path : str | None, optional
        Destination file path for the sanitized GeoJSON. If provided, the file is written.
    precision : int, default 6
        Number of coordinate decimal places (~0.1m resolution at 6 decimals).
    dedup_reciprocal : bool, default True
        Whether to drop reciprocal directed edge twins (v->u) with identical properties.
    columns : list[str] | None, optional
        List of property columns to retain. Defaults to FRONTEND_PROPERTIES.

    Returns
    -------
    gpd.GeoDataFrame
        The sanitized and compacted GeoDataFrame.
    """
    target_columns = FRONTEND_PROPERTIES if columns is None else columns

    # 1. Identify available property columns and retain geometry
    available_props = [
        c for c in target_columns if c in edges.columns and c != "geometry"
    ]

    # 2. Extract u, v for reciprocal deduplication if requested and available
    has_uv = False
    u_vals, v_vals = None, None
    if dedup_reciprocal:
        if (
            isinstance(edges.index, pd.MultiIndex)
            and "u" in edges.index.names
            and "v" in edges.index.names
        ):
            u_vals = edges.index.get_level_values("u")
            v_vals = edges.index.get_level_values("v")
            has_uv = True
        elif "u" in edges.columns and "v" in edges.columns:
            u_vals = edges["u"].tolist()
            v_vals = edges["v"].tolist()
            has_uv = True

    # 3. Clean property values: unpack arrays/lists and convert NaNs to None
    clean_dict: dict[str, list] = {}
    for col in available_props:
        series = edges[col]
        cleaned: list = []
        for x in series:
            if isinstance(x, (list, np.ndarray)):
                if col == "name" and len(x) > 1:
                    val = " / ".join(str(s) for s in x if s)
                elif len(x) > 0:
                    val = x[0]
                else:
                    val = None
            elif pd.isna(x):
                val = None
            else:
                val = x
            cleaned.append(val)
        clean_dict[col] = cleaned

    clean_dict["geometry"] = edges.geometry.values
    sanitized = gpd.GeoDataFrame(clean_dict, crs=edges.crs)

    # 4. Snap coordinates to target precision (~0.1m for precision=6)
    if len(sanitized) > 0:
        grid_size = 10 ** (-precision)
        sanitized.geometry = shapely.set_precision(
            sanitized.geometry, grid_size=grid_size
        )

    # 5. Deduplicate reciprocal edges (v->u) with identical properties and reverse geometry
    # OSMnx directed graphs store both forward (u -> v) and backward (v -> u) edges for two-way streets.
    # We only drop an edge if an already-kept edge runs in the opposite direction (u0 == v and v0 == u),
    # has identical stress model properties, and has exact reverse geometry.
    # This preserves same-direction parallel multi-edges (e.g. distinct carriageways between merged nodes),
    # self-loops (u == v), and any edge pairs with differing properties (e.g. asymmetric bike lanes).
    if has_uv and u_vals is not None and v_vals is not None and len(sanitized) > 0:
        prop_tuples = list(zip(*(clean_dict[c] for c in available_props)))
        geoms = sanitized.geometry.tolist()
        edges_by_direction: dict[tuple, list[tuple[int, shapely.Geometry, tuple]]] = (
            collections.defaultdict(list)
        )
        keep_mask: list[bool] = [True] * len(sanitized)

        for idx, (u, v, geom, props) in enumerate(
            zip(u_vals, v_vals, geoms, prop_tuples)
        ):
            if u == v or geom is None or geom.is_empty:
                # Preserve self-loops and empty geoms as-is
                continue

            opposite_candidates = edges_by_direction.get((v, u), [])
            if opposite_candidates:
                rev_geom = shapely.reverse(geom)
                for cand_idx, cand_geom, cand_props in opposite_candidates:
                    if keep_mask[cand_idx] and cand_props == props:
                        # Tolerance 1e-7 on snapped coordinates ensures exact geometric match
                        if cand_geom.equals_exact(rev_geom, 1e-7):
                            keep_mask[idx] = False
                            break

            if keep_mask[idx]:
                edges_by_direction[(u, v)].append((idx, geom, props))

        sanitized = sanitized[keep_mask].reset_index(drop=True)
    else:
        sanitized = sanitized.reset_index(drop=True)

    # 6. Export to minified GeoJSON if out_path is provided
    if out_path is not None:
        parent_dir = os.path.dirname(out_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        geojson_str = sanitized.to_json(
            drop_id=True, show_bbox=False, separators=(",", ":")
        )
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(geojson_str)

    return sanitized
