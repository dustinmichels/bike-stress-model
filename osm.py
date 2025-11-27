import re

import numpy as np
import osmnx as ox
import pandas as pd

from util import extract_maxspeed, extract_width, first_if_list

# add cycleway to useful tags
ox.settings.useful_tags_way = ox.settings.useful_tags_way + ["cycleway"]


def get_network(place: str, network_type: str):
    G = ox.graph_from_place(place, network_type=network_type)
    nodes, edges = ox.graph_to_gdfs(G)
    return nodes, edges


def process_network(edges: pd.DataFrame) -> pd.DataFrame:
    # drop some unneeded columns
    edges = edges.drop(
        ["ref", "service", "access", "bridge", "tunnel", "junction"], axis=1
    )

    # flatten rows if they contain lists
    rows_to_flatten = ["highway", "lanes", "cycleway"]
    for col in rows_to_flatten:
        edges[col] = first_if_list(edges[col])

    # parse maxspeed and width
    edges["maxspeed_int"] = edges["maxspeed"].apply(extract_maxspeed).astype("Int64")
    edges["width_float"] = edges["width"].apply(extract_width).astype("Float64")

    # if width is missing, set to 10 meters
    edges["width_float"] = edges["width_float"].fillna(10.0)

    # add buffer column (half of width)
    edges["buffer_dist"] = edges["width_float"] / 2.0

    return edges


def main():
    place = "Somerville, Massachusetts, USA"
    print("Get bike network")
    nodes, edges = get_network(place, "bike")

    print("Process network")
    edges_bike = process_network(edges)

    print("Saving to GeoPackage")
    edges_bike.to_file(
        "data/somerville_network.gpkg", layer="somerville_streets", driver="GPKG"
    )


if __name__ == "__main__":
    main()
