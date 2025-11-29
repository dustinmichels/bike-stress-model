import os
from datetime import date, timedelta

import duckdb
import geopandas as gpd
import kagglehub
import pandas as pd
from shapely.geometry import Point


def download_data_return_path() -> str:
    """
    Downloads the US Accidents dataset (if updated),
    returns the path to a Parquet file (creates it if it doesn't exist).
    """

    # Step 1: Download the CSV (fresh copy)
    dataset_path = kagglehub.dataset_download("sobhanmoosavi/us-accidents")
    print(f"Dataset path: {dataset_path}")

    # Find CSV files
    files = os.listdir(dataset_path)
    csv_files = [f for f in files if f.lower().endswith(".csv")]
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV file found in {dataset_path}. Files present: {files}"
        )

    csv_path = os.path.join(dataset_path, csv_files[0])
    print(f"CSV file path: {csv_path}")

    # Step 2: Check if a matching Parquet file exists
    parquet_path = os.path.splitext(csv_path)[0] + ".parquet"
    if os.path.exists(parquet_path):
        print(f"Parquet already exists: {parquet_path}")
        return parquet_path

    # Step 3: Create Parquet using DuckDB
    print(f"No Parquet found, creating at: {parquet_path}")
    duckdb.query(f"""
        COPY (SELECT * FROM '{csv_path}') 
        TO '{parquet_path}' (FORMAT PARQUET)
    """)

    return parquet_path


def load_duckdb_from_path(path):
    if path.lower().endswith(".parquet"):
        return duckdb.read_parquet(path)
    elif path.lower().endswith(".csv"):
        return duckdb.read_csv(path, parallel=True)
    else:
        raise ValueError(f"Unsupported file format for path: {path}")


def load_data():
    path = download_data_return_path()
    return load_duckdb_from_path(path)


def filter_data(data, bbox: tuple, years: int = 4) -> pd.DataFrame:
    """
    Filters the data for accidents within the bounding box and within the last 'years' years.
    bbox: (min_lng, min_lat, max_lng, max_lat)
    """

    n_years_ago = date.today().replace(year=date.today().year - years)
    filtered = data.filter(
        f"""
    Start_Lng BETWEEN {bbox[0]} AND {bbox[2]}
    AND Start_Lat BETWEEN {bbox[1]} AND {bbox[3]}
    AND Start_Time >= DATE '{n_years_ago}'
    """
    )
    return filtered.df()


def make_geospatial(df):
    # rename Start_Lat and Start_Lng to Latitude and Longitude
    df = df.rename(columns={"Start_Lat": "Latitude", "Start_Lng": "Longitude"})

    # First, make sure lat/lon are numeric
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")

    # Drop rows with missing coordinates
    df = df.dropna(subset=["Latitude", "Longitude"])

    # Create Point geometry from lon/lat
    geometry = [Point(xy) for xy in zip(df["Longitude"], df["Latitude"])]

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry=geometry)

    # Set CRS to WGS84 (EPSG:4326)
    gdf.set_crs(epsg=4326, inplace=True)

    # Convert to EPSG:26986 (Massachusetts Mainland)
    gdf = gdf.to_crs(epsg=26986)

    # Optional: save to a file
    # gdf.to_file("data/crashes.geojson", driver="GeoJSON")

    return gdf


def main():
    data = load_data()

    # Somerville, MA
    bbox = (-71.134457, 42.3731775, -71.0753392, 42.4180395)

    filtered_data = filter_data(data, years=4, bbox=bbox)
