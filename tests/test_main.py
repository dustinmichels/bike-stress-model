import os

from main import copy_to_frontend


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

    places = ["Somerville, Massachusetts, USA", "Unknown City, USA"]

    copied = copy_to_frontend(
        places=places,
        out_path=str(out_dir),
        dest_dir=str(dest_dir),
        chart_dest_dir=str(chart_dest_dir),
    )

    # Only somerville_streets.geojson should be copied to dest_dir
    assert len(copied) == 1
    assert os.path.exists(dest_dir / "somerville_streets.geojson")
    # Boundary file should not be copied
    assert not os.path.exists(dest_dir / "somerville_boundary.geojson")
