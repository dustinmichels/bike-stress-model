import geopandas as gpd
import networkx as nx
import osmnx as ox
import pandas as pd
from shapely.geometry import LineString, Point
from tqdm import tqdm


def get_route_gdf(G, start_coord, end_coord, weight="composite_score"):
    """
    Compute a route between two points on a graph G, using the specified weight.
    Returns a GeoDataFrame with route geometry and average weight value.

    Parameters:
    - G: networkx graph (OSMnx graph)
    - start_coord: tuple (x, y) OR shapely.geometry.Point
    - end_coord: tuple (x, y) OR shapely.geometry.Point
    - weight: str, edge attribute to use as weight (default: "composite_score")
              Common options: "composite_score", "length"

    Returns:
    - GeoDataFrame with columns: ['type', 'geometry', weight column name]
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

    # --- 4. Extract edge weights ---
    route_edges = list(zip(route[:-1], route[1:]))
    edge_weights = []

    for u, v in route_edges:
        data = G.get_edge_data(u, v)
        if data is not None:
            edge = list(data.values())[0]
            edge_weights.append(edge.get(weight, 0))
        else:
            edge_weights.append(0)

    avg_weight = sum(edge_weights) / len(edge_weights) if edge_weights else None

    # --- 5. Create geometries ---
    route_coords = [(G.nodes[n]["x"], G.nodes[n]["y"]) for n in route]
    route_geom = LineString(route_coords)

    # --- 6. Create GeoDataFrame ---
    gdf = gpd.GeoDataFrame(
        [
            {"geometry": route_geom, weight: avg_weight},
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
            route_gdf["from_block_id"] = row["GEOID20"]
            route_gdf["to_school_name"] = school["Name"]
            route_gdf["to_school_id"] = school["GlobalID"]
            dataframes.append(route_gdf)

    combined_gdf = gpd.GeoDataFrame(
        pd.concat(dataframes, ignore_index=True), crs=use_crs
    )
    return combined_gdf, errors
