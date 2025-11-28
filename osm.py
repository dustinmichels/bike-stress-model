import osmnx as ox
import pandas as pd

import src.stressmodel as stressmodel
from util import extract_width, first_if_list

OUT_PATH = "data/out/somerville_network"

# add cycleway to useful tags
ox.settings.useful_tags_way = ox.settings.useful_tags_way + [
    "massgis:way_id",
    "condition",
    "surface",
    "bicycle",
    "cycleway",
    "cycleway:left",
    "cycleway:right",
    "cycleway:both",
    "cycleway:buffer",
    "cycleway:separation",
    "sidewalk:left",
    "sidewalk:right",
    "sidewalk:both",
    "parking:left",
    "parking:right",
    "parking:both",
]


def get_network(place: str, network_type: str = "bike"):
    G = ox.graph_from_place(place, network_type=network_type)

    # project graph to EPSG:26986 (Massachusetts Mainland)
    # G = ox.project_graph(G, to_crs="EPSG:26986")

    nodes, edges = ox.graph_to_gdfs(G)
    return nodes, edges


def process_network(edges: pd.DataFrame) -> pd.DataFrame:
    # drop some unneeded columns
    edges = edges.drop(
        ["ref", "service", "access", "bridge", "tunnel", "junction"], axis=1
    )

    # flatten rows if they contain lists
    # TODO: this should be chose best
    rows_to_flatten = ["highway", "lanes"]
    for col in rows_to_flatten:
        edges[col] = first_if_list(edges[col])

    # parse width
    edges["width_float"] = edges["width"].apply(extract_width).astype("Float64")

    # if width is missing, set to 10 meters
    edges["width_float"] = edges["width_float"].fillna(10.0)

    # add buffer column (half of width)
    edges["width_half"] = edges["width_float"] / 2.0

    # sort columns alphabetically
    edges = edges.reindex(sorted(edges.columns), axis=1)

    return edges


def main():
    place = "Somerville, Massachusetts, USA"
    print("Get bike network")
    nodes, edges = get_network(place, "bike")

    print("Process network")
    edges = process_network(edges)

    # MODEL - SPEED: parse maxspeed
    print("Prepare speed data")
    edges["maxspeed_int"], edges["maxspeed_int_score"] = stressmodel.speed.run(edges)

    # MODEL - SEPARATION LEVEL: combine cycleway types
    print("Prepare separation level data")
    edges["separation_level"], edges["separation_level_score"] = (
        stressmodel.separation_level.run(edges)
    )

    # save to csv
    print("Saving to CSV")
    edges.to_csv(f"{OUT_PATH}_edges.csv", index=False)

    print("Saving to GeoPackage")
    edges.to_file(f"{OUT_PATH}.gpkg", layer="somerville_streets", driver="GPKG")
    nodes.to_file(f"{OUT_PATH}.gpkg", layer="somerville_nodes", driver="GPKG")

    # also save geojson
    print("Saving to GeoJSON")
    edges.to_file(f"{OUT_PATH}.geojson", driver="GeoJSON")


if __name__ == "__main__":
    main()
