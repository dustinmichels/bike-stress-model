import geopandas as gpd
import networkx as nx
import osmnx as ox
import pandas as pd
from shapely.geometry import LineString, Point
from tqdm import tqdm


def get_route_gdf(G, start_coord, end_coord, weight="composite_score"):
    """
    Compute a route between two points on a graph G, using the specified weight.
    Returns a GeoDataFrame with route geometry and statistics.

    Parameters:
    - G: networkx graph (OSMnx graph)
    - start_coord: tuple (x, y) OR shapely.geometry.Point
    - end_coord: tuple (x, y) OR shapely.geometry.Point
    - weight: str, edge attribute to use as weight (default: "composite_score")
              Common options: "composite_score", "length"

    Returns:
    - GeoDataFrame with columns: ['geometry', 'mean_composite_score',
      'median_composite_score', 'min_composite_score', 'max_composite_score',
      'sum_length']
    """

    use_crs = G.graph["crs"] if "crs" in G.graph else "EPSG:4326"

    # --- 1. Convert start/end to x, y ---
    if isinstance(start_coord, Point):
        start_x, start_y = start_coord.x, start_coord.y
    else:  # assume tuple (x, y)
        start_x, start_y = start_coord

    if isinstance(end_coord, Point):
        end_x, end_y = end_coord.x, end_coord.y
    else:
        end_x, end_y = end_coord

    # --- 2. Nearest nodes ---
    orig = ox.nearest_nodes(G, X=start_x, Y=start_y)
    dest = ox.nearest_nodes(G, X=end_x, Y=end_y)

    # --- 3. Shortest path ---
    route = ox.shortest_path(G, orig, dest, weight=weight)

    if route is None:
        raise ValueError("No route found between start and end")

    # --- 4. Extract edge data ---
    route_edges = list(zip(route[:-1], route[1:]))
    composite_scores = []
    lengths = []

    for u, v in route_edges:
        data = G.get_edge_data(u, v)
        if data is not None:
            edge = list(data.values())[0]
            composite_scores.append(edge.get("composite_score", 0))
            lengths.append(edge.get("length", 0))
        else:
            composite_scores.append(0)
            lengths.append(0)

    # --- 5. Calculate statistics ---
    mean_composite = (
        sum(composite_scores) / len(composite_scores) if composite_scores else None
    )
    median_composite = (
        sorted(composite_scores)[len(composite_scores) // 2]
        if composite_scores
        else None
    )
    min_composite = min(composite_scores) if composite_scores else None
    max_composite = max(composite_scores) if composite_scores else None
    sum_length = sum(lengths)

    # --- 6. Create geometries ---
    route_coords = [(G.nodes[n]["x"], G.nodes[n]["y"]) for n in route]
    route_geom = LineString(route_coords)

    # --- 7. Create GeoDataFrame ---
    gdf = gpd.GeoDataFrame(
        [
            {
                "geometry": route_geom,
                "mean_composite_score": mean_composite,
                "median_composite_score": median_composite,
                "min_composite_score": min_composite,
                "max_composite_score": max_composite,
                "sum_length": sum_length,
            },
        ],
        crs=use_crs,
    )

    return gdf


def compute_routes_from_census_blocks_to_school(
    G: nx.classes.multidigraph.MultiDiGraph,
    somerville_census_blocks: gpd.GeoDataFrame,
    school: pd.Series,
    weight: str = "composite_score",
):
    """
    Iterate over census blocks centroids GeoDataFrame and compute routes to the given school.

    Parameters:
    - G: networkx graph (OSMnx graph)
    - somerville_census_blocks: GeoDataFrame with census blocks centroids
    - school: pd.Series with school information (must contain 'geometry', 'Name', '
        GlobalID' fields)
    - weight: str, edge attribute to use as weight (default: "composite_score" | "length")
    """

    errors = []
    dataframes = []

    use_crs = G.graph["crs"] if "crs" in G.graph else "EPSG:4326"

    for i, row in tqdm(
        somerville_census_blocks.iterrows(), total=len(somerville_census_blocks)
    ):
        orig_point = row["geometry"]
        dest_point = school["geometry"]
        try:
            route_gdf = get_route_gdf(G, orig_point, dest_point, weight=weight)
        except Exception as e:
            errors.append(f"Error on index {i}: {e}")
            route_gdf = gpd.GeoDataFrame()

        if not route_gdf.empty:
            route_gdf["from_block_geoid"] = row["GEOID20"]
            route_gdf["from_blkgrp20"] = row["BLKGRP20"]
            route_gdf["from_tract20"] = row["TRACT20"]
            route_gdf["to_school_name"] = school["Name"]
            route_gdf["to_school_id"] = school["GlobalID"]
            dataframes.append(route_gdf)

    combined_gdf = gpd.GeoDataFrame(
        pd.concat(dataframes, ignore_index=True), crs=use_crs
    )
    return combined_gdf, errors


def compute_routes_from_census_blocks_to_all_schools(
    G: nx.classes.multidigraph.MultiDiGraph,
    somerville_census_blocks: gpd.GeoDataFrame,
    schools_gdf: gpd.GeoDataFrame,
    weight="composite_score",
):
    """
    Compute routes from census blocks to all schools and aggregate results.

    Parameters
    ----------
    schools_gdf : GeoDataFrame
        GeoDataFrame containing school locations and attributes
    G : networkx.classes.multidigraph.MultiDiGraph
        Street network graph
    somerville_census_blocks : GeoDataFrame
        Census blocks to route from
    weight : str, optional
        Edge weight to use for routing. Must be "composite_score" or "length".
        Default is "composite_score".

    Returns
    -------
    all_routes_gdf : GeoDataFrame
        Aggregated GeoDataFrame of all routes from census blocks to schools
    errors : list
        List of error messages encountered during routing
    """
    if weight not in ["composite_score", "length"]:
        raise ValueError("weight must be 'composite_score' or 'length'")

    all_routes = []  # accumulate all GeoDataFrames

    for i, school in schools_gdf.iterrows():
        print(f"----- {school['Name']} -----")

        combined_gdf, errors = compute_routes_from_census_blocks_to_school(
            G, somerville_census_blocks, school, weight=weight
        )

        # add school name column
        combined_gdf = combined_gdf.assign(school_name=school["Name"])

        # collect for global merge
        all_routes.append(combined_gdf)

    # merge all routes into one GeoDataFrame
    all_routes_gdf = gpd.GeoDataFrame(
        pd.concat(all_routes, ignore_index=True), crs=all_routes[0].crs
    )

    return all_routes_gdf, errors
