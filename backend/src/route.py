import geopandas as gpd
import osmnx as ox
from shapely.geometry import LineString, Point


def get_route_gdf(G, start_coord, end_coord):
    """
    Compute a route between two points on a graph G, using 'composite_score' as weight.
    Returns a GeoDataFrame with start, end, and route geometries and average composite score.

    Parameters:
    - G: networkx graph (OSMnx graph)
    - start_coord: tuple (x, y) OR shapely.geometry.Point
    - end_coord: tuple (x, y) OR shapely.geometry.Point

    Returns:
    - GeoDataFrame with columns: ['type', 'geometry', 'composite_score']
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

    # Print the node ID
    # print(f"Nearest node ID: {orig}")

    # --- 3. Shortest path ---
    route = ox.shortest_path(G, orig, dest, weight="composite_score")

    if route is None:
        raise ValueError("No route found between start and end")

    # --- 4. Extract edge scores ---
    #   route[:-1] gives all nodes except the last → [1, 5, 7]
    #   route[1:] gives all nodes except the first → [5, 7, 12]
    #   zip(route[:-1], route[1:]) pairs each consecutive node to represent edges:
    #       [(1, 5), (5, 7), (7, 12)]
    #   loop through these edges to get their composite scores
    route_edges = list(zip(route[:-1], route[1:]))
    edge_scores = []

    for u, v in route_edges:
        data = G.get_edge_data(u, v)
        if data is not None:
            edge = list(data.values())[0]
            edge_scores.append(edge.get("composite_score", 0))
        else:
            edge_scores.append(0)

    avg_score = sum(edge_scores) / len(edge_scores) if edge_scores else None

    # --- 5. Create geometries ---
    route_coords = [(G.nodes[n]["x"], G.nodes[n]["y"]) for n in route]
    route_geom = LineString(route_coords)

    # --- 6. Create GeoDataFrame ---
    gdf = gpd.GeoDataFrame(
        [
            {"geometry": route_geom, "composite_score": avg_score},
        ],
        crs=use_crs,
    )

    return gdf
