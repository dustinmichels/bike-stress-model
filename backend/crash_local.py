import duckdb
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point


def filter_crash_data(df: pd.DataFrame) -> pd.DataFrame:
    con = duckdb.connect(database=":memory:")

    # Filter rows from the last 3 years, casting the date column to TIMESTAMP
    filtered_df = con.execute("""
        SELECT *
        FROM df
        WHERE CAST("Date and Time of Crash" AS TIMESTAMP) 
            >= date_trunc('day', current_date - INTERVAL '3 years')
    """).df()

    return filtered_df


def parse_crash_data():
    df = pd.read_csv("data/raw/Police_Data__Crashes.csv")

    print("Filtering crash data to last 3 years")
    df = filter_crash_data(df)

    # Assume df is your DataFrame with Latitude and Longitude columns
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
    gdf.to_file("data/police_crashes.geojson", driver="GeoJSON")


if __name__ == "__main__":
    parse_crash_data()
