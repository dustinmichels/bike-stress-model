import os

from main import Place, copy_to_frontend, save_data_for_place


def test_copy_to_frontend(tmp_path):
    out_dir = tmp_path / "out"
    dest_dir = tmp_path / "frontend"
    chart_dest_dir = tmp_path / "deployed-charts"
    out_dir.mkdir()

    # Create dummy street geojson and boundary geojson
    somerville_street = out_dir / "somerville_streets.geojson"
    somerville_street.write_text('{"type": "FeatureCollection", "features": []}')
    somerville_boundary = out_dir / "somerville_boundary.geojson"
    somerville_boundary.write_text('{"type": "FeatureCollection", "features": []}')

    places = [
        Place(name="Somerville, Massachusetts, USA", residential_default_mph=20),
        Place(name="Unknown City, USA", residential_default_mph=25),
    ]

    copied = copy_to_frontend(
        places=places,
        out_path=str(out_dir),
        dest_dir=str(dest_dir),
        chart_dest_dir=str(chart_dest_dir),
    )

    # Only somerville_streets.geojson should be copied to dest_dir
    assert copied == [str(dest_dir / "somerville_streets.geojson")]
    assert os.path.exists(dest_dir / "somerville_streets.geojson")
    # Boundary file should not be copied
    assert not os.path.exists(dest_dir / "somerville_boundary.geojson")


def test_save_data_for_place(tmp_path):
    import geopandas as gpd
    import shapely.geometry as sg

    out_dir = str(tmp_path / "out")
    nodes = gpd.GeoDataFrame({"geometry": [sg.Point(0, 0)]}, crs="EPSG:4326")
    edges = gpd.GeoDataFrame(
        {
            "name": ["Test Road"],
            "separation_level": ["lane"],
            "street_classification": ["residential"],
            "maxspeed_int": [25.0],
            "composite_score": ["2.0"],
            "geometry": [sg.LineString([(0, 0), (1, 1)])],
        },
        crs="EPSG:4326",
    )

    place = Place(name="Somerville, Massachusetts, USA", residential_default_mph=20)
    save_data_for_place(place, out_dir, nodes, edges)

    gpkg_path = os.path.join(out_dir, "somerville_streets.gpkg")
    geojson_path = os.path.join(out_dir, "somerville_streets.geojson")

    assert os.path.exists(gpkg_path)
    assert os.path.exists(geojson_path)

    # Verify GeoJSON was sanitized (composite_score pruned)
    saved_geojson = gpd.read_file(geojson_path)
    assert "composite_score" not in saved_geojson.columns
    assert saved_geojson["name"].iloc[0] == "Test Road"
