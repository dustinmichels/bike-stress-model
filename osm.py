import re

import numpy as np
import osmnx as ox
import pandas as pd

FEET_TO_M = 0.3048


def extract_maxspeed(x) -> float:
    # Handle NaN early
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return np.nan

    # Handle lists and numpy arrays uniformly
    if isinstance(x, (list, np.ndarray)):
        speeds = [extract_maxspeed(i) for i in x]
        # filter out NaNs
        speeds = [s for s in speeds if not pd.isna(s)]
        return max(speeds) if speeds else np.nan

    # Convert to string and extract digits
    x_str = str(x)
    nums = re.findall(r"\d+", x_str)

    return int(max(nums, key=int)) if nums else np.nan


def extract_width(value):
    # If list, use first value
    if isinstance(value, list):
        value = value[0]

    """Return numeric width in meters from OSM width tags."""
    if pd.isna(value):
        return None

    s = str(value).strip()

    # Feet notation like 9'
    if "'" in s:
        match = re.search(r"\d+(\.\d+)?", s)
        if match:
            return float(match.group()) * FEET_TO_M
        else:
            return None

    # Standard numeric meters
    match = re.search(r"\d+(\.\d+)?", s)
    if match:
        return float(match.group())

    return None


def get_network(place: str, network_type: str):
    G = ox.graph_from_place(place, network_type=network_type)
    _, edges = ox.graph_to_gdfs(G)
    edges["maxspeed_int"] = edges["maxspeed"].apply(extract_maxspeed)
    edges["width_float"] = edges["width"].apply(extract_width)
    return edges


def main():
    place = "Somerville, Massachusetts, USA"

    print("Get bike network")
    edges_bike = get_network(place, "bike")

    print("Get drive network")
    edges_drive = get_network(place, "drive")

    print("Saving to GeoPackage")
    outfp = "data/somerville.gpkg"
    edges_bike.to_file(outfp, layer="bike_edges", driver="GPKG")
    edges_drive.to_file(outfp, layer="drive_edges", driver="GPKG")


if __name__ == "__main__":
    main()
