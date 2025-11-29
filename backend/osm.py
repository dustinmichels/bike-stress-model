import os
import shutil

import osmnx as ox
import pandas as pd

import src.stressmodel as sm
from util import extract_width, first_if_list

OUT_PATH = "data/out"

PLACES = [
    "Somerville, Massachusetts, USA",
    "Cambridge, Massachusetts, USA",
    "Boulder, Colorado, USA",
]

# add cycleway to useful tags
ox.settings.useful_tags_way = ox.settings.useful_tags_way + [
    "massgis:way_id",
    "condition",
    "smoothness",
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

    # parse width
    edges["width_float"] = edges["width"].apply(extract_width).astype("Float64")

    # if width is missing, set to 10 meters
    edges["width_float"] = edges["width_float"].fillna(10.0)

    # add buffer column (half of width)
    edges["width_half"] = edges["width_float"] / 2.0

    # sort columns alphabetically
    edges = edges.reindex(sorted(edges.columns), axis=1)

    return edges


def prepare_data_for_place(place: str):
    print(f"> Getting bike network for {place}")
    nodes, edges = get_network(place, "bike")

    print(f"> Processing network for {place}")
    edges = process_network(edges)

    # MODEL - SPEED: parse maxspeed
    print(f"> MODEL: Preparing speed data for {place}")
    edges["maxspeed_int"], edges["maxspeed_int_score"] = sm.speed.run(edges)

    # MODEL - SEPARATION LEVEL: combine cycleway types
    print(f"> MODEL: Preparing separation level data for {place}")
    edges["separation_level"], edges["separation_level_score"] = (
        sm.separation_level.run(edges)
    )

    # MODEL - CATEGORY: classify street types
    print(f"> MODEL: Preparing street category data for {place}")
    edges["street_classification"], edges["street_classification_score"] = (
        sm.classification.run(edges)
    )

    # MODEL - LANES: parse number of lanes
    print(f"> MODEL: Preparing lanes data for {place}")
    edges["lanes_int"], edges["lanes_int_score"] = sm.lanes.run(edges)

    # TODO: condition (combo of smoothness and condition?) - condition is not standard
    # TODO: number of lanes (ideally in direction of travel)

    # copy some OG vals so they are easy to compare with new vals
    edges["street_0"] = edges["highway"]
    edges["maxspeed_0"] = edges["maxspeed"]
    edges["lanes_0"] = edges["lanes"]

    # sort columns alphabetically again
    edges = edges.reindex(sorted(edges.columns), axis=1)

    # compute composite score
    print(f"> MODEL: Preparing composite score for {place}")

    scores = [
        "maxspeed_int_score",
        "separation_level_score",
        "street_classification_score",
        "lanes_int_score",
    ]
    edges["composite_score"] = edges[scores].sum(axis=1) / len(scores)

    return nodes, edges


def save_data_for_place(place: str, out_path: str, nodes, edges):
    place_first_word = place.split(",")[0].replace(" ", "_").lower()
    out_path = f"{out_path}/{place_first_word}"

    # save to csv
    print(f"> Saving edges to CSV for {place}")
    edges.to_csv(f"{out_path}_streets.csv", index=True)

    # also save to GeoPackage
    print(f"> Saving edges and nodes to GeoPackage for {place}")
    edges.to_file(f"{out_path}_streets.gpkg", layer="streets", driver="GPKG")
    nodes.to_file(f"{out_path}_streets.gpkg", layer="nodes", driver="GPKG")

    # also save geojson
    print(f"> Saving edges to GeoJSON for {place}")
    edges.to_file(f"{out_path}_streets.geojson", driver="GeoJSON")


def main():
    # delete contents of data/out directory
    print("> Clearing data/out")
    if os.path.exists(OUT_PATH):
        shutil.rmtree(OUT_PATH)
    os.makedirs(OUT_PATH, exist_ok=True)

    for place in PLACES:
        nodes, edges = prepare_data_for_place(place)
        save_data_for_place(place, OUT_PATH, nodes, edges)


if __name__ == "__main__":
    main()
