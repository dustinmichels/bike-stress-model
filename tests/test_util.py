import os

import numpy as np
import pandas as pd
import pytest

from src.stressmodel.speed import extract_maxspeed
from util import (
    FEET_TO_M,
    extract_width,
    sanitize_for_frontend,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("25 mph", 25.0),
        ("30", 30.0),
        ("  30mph  ", 30.0),
    ],
)
def test_extract_maxspeed_formats(value, expected):
    assert extract_maxspeed(value) == expected


def test_extract_maxspeed_rejects_invalid_value():
    assert np.isnan(extract_maxspeed("invalid"))


def test_extract_maxspeed_preserves_missing_value():
    assert np.isnan(extract_maxspeed(np.nan))


def test_extract_maxspeed_uses_highest_list_value():
    assert extract_maxspeed(["25 mph", "30 mph", "20 mph"]) == 30.0


def test_extract_maxspeed_rejects_empty_list():
    assert np.isnan(extract_maxspeed([]))


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("3.5", 3.5),
        ("3.5 m", 3.5),
        ("12.5'", 12.5 * FEET_TO_M),
        ("9'6\"", 9.5 * FEET_TO_M),
    ],
)
def test_extract_width_formats(value, expected):
    assert extract_width(value) == pytest.approx(expected)


def test_extract_width_preserves_missing_value():
    assert pd.isna(extract_width(np.nan))


def test_extract_width_rejects_invalid_value():
    assert pd.isna(extract_width("unknown"))


def test_extract_width_uses_highest_list_value():
    assert extract_width(["3.5", "4.0"]) == 4.0


class TestSanitizeForFrontend:
    """Test suite for sanitize_for_frontend function."""

    def test_pruning_unneeded_columns(self):
        import geopandas as gpd
        import shapely.geometry as sg

        df = gpd.GeoDataFrame(
            {
                "name": ["Beacon St"],
                "separation_level": ["lane"],
                "street_classification": ["residential"],
                "maxspeed_int": [25.0],
                "lanes_int": [2],
                # Unneeded columns that must be pruned:
                "composite_score": ["2.5"],
                "separation_level_score": [2.0],
                "street_classification_score": [2.0],
                "maxspeed_int_score": [2.0],
                "length": [123.456789],
                "width_float": [10.0],
                "width_half": [5.0],
                "street_0": ["residential"],
                "maxspeed_0": ["25 mph"],
                "geometry": [sg.LineString([(0, 0), (1, 1)])],
            },
            crs="EPSG:4326",
        )

        sanitized = sanitize_for_frontend(df)
        assert set(sanitized.columns) == {
            "name",
            "separation_level",
            "street_classification",
            "maxspeed_int",
            "lanes_int",
            "geometry",
        }

    def test_value_unpacking_and_cleaning(self):
        import geopandas as gpd
        import shapely.geometry as sg

        df = gpd.GeoDataFrame(
            {
                "name": [np.array(["Main St"]), ["Second St"], np.nan],
                "separation_level": ["track", None, "none"],
                "street_classification": ["residential", "medium-capacity", None],
                "maxspeed_int": [20.0, np.nan, 30.0],
                "geometry": [
                    sg.LineString([(0, 0), (1, 1)]),
                    sg.LineString([(1, 1), (2, 2)]),
                    sg.LineString([(2, 2), (3, 3)]),
                ],
            },
            crs="EPSG:4326",
        )

        sanitized = sanitize_for_frontend(df)
        assert sanitized["name"].iloc[0] == "Main St"
        assert isinstance(sanitized["name"].iloc[0], str)
        assert sanitized["name"].iloc[1] == "Second St"
        assert pd.isna(sanitized["name"].iloc[2])
        assert pd.isna(sanitized["maxspeed_int"].iloc[1])
        import json

        serialized = json.loads(sanitized.to_json())
        assert serialized["features"][2]["properties"]["name"] is None
        assert serialized["features"][1]["properties"]["maxspeed_int"] is None

    def test_precision_snapping(self):
        import geopandas as gpd
        import shapely.geometry as sg

        df = gpd.GeoDataFrame(
            {
                "name": ["Precise St"],
                "geometry": [
                    sg.LineString(
                        [
                            (-71.093904212345678, 42.382206312345678),
                            (-71.093538212345678, 42.381965712345678),
                        ]
                    )
                ],
            },
            crs="EPSG:4326",
        )

        sanitized = sanitize_for_frontend(df, precision=6)
        coords = list(sanitized.geometry.iloc[0].coords)
        assert coords == [(-71.093904, 42.382206), (-71.093538, 42.381966)]

    def test_reciprocal_edge_deduplication(self):
        import geopandas as gpd
        import shapely
        import shapely.geometry as sg

        # Edges 1 & 2: identical bidirectional twins -> edge 2 should be dropped
        # Edge 3 & 4: opposite direction but DIFFERENT properties (track vs none) -> both kept
        # Edge 5 & 6: same direction parallel edges with different geometries -> both kept
        # Edge 7: self-loop (u == v) -> kept
        idx = pd.MultiIndex.from_tuples(
            [
                (1, 2, 0),
                (2, 1, 0),
                (3, 4, 0),
                (4, 3, 0),
                (5, 6, 0),
                (5, 6, 1),
                (7, 7, 0),
            ],
            names=["u", "v", "key"],
        )

        df = gpd.GeoDataFrame(
            {
                "name": [
                    "Twin St",
                    "Twin St",
                    "Asym St",
                    "Asym St",
                    "Parallel St",
                    "Parallel St",
                    "Loop St",
                ],
                "separation_level": [
                    "lane",
                    "lane",
                    "track",
                    "none",
                    "none",
                    "none",
                    "none",
                ],
                "street_classification": ["residential"] * 7,
                "maxspeed_int": [25.0] * 7,
                "geometry": [
                    sg.LineString([(0, 0), (1, 1)]),
                    sg.LineString([(1, 1), (0, 0)]),
                    sg.LineString([(2, 2), (3, 3)]),
                    sg.LineString([(3, 3), (2, 2)]),
                    sg.LineString([(4, 4), (5, 5)]),
                    sg.LineString([(4, 4), (4.5, 4.8), (5, 5)]),  # Different shape
                    sg.LineString([(6, 6), (6.1, 6.1), (6, 6)]),  # Self-loop
                ],
            },
            index=idx,
            crs="EPSG:4326",
        )

        sanitized = sanitize_for_frontend(df)
        # Total original: 7. Exactly 1 identical twin dropped -> 6 remain
        assert len(sanitized) == 6
        assert "Twin St" in sanitized["name"].values
        assert len(sanitized[sanitized["name"] == "Twin St"]) == 1
        assert len(sanitized[sanitized["name"] == "Asym St"]) == 2
        assert len(sanitized[sanitized["name"] == "Parallel St"]) == 2
        assert len(sanitized[sanitized["name"] == "Loop St"]) == 1

        # Total spatial network length (union_all) must be 100% identical
        union_orig = shapely.union_all(df.geometry)
        union_sanitized = shapely.union_all(sanitized.geometry)
        assert abs(union_orig.length - union_sanitized.length) < 1e-9

    def test_out_path_export(self, tmp_path):
        import geopandas as gpd
        import shapely.geometry as sg

        out_file = str(tmp_path / "test_out.geojson")
        df = gpd.GeoDataFrame(
            {
                "name": ["Export St"],
                "separation_level": ["lane"],
                "street_classification": ["residential"],
                "maxspeed_int": [25.0],
                "geometry": [
                    sg.LineString([(0.1234567, 0.7654321), (1.1111111, 2.2222222)])
                ],
            },
            crs="EPSG:4326",
        )

        sanitize_for_frontend(df, out_path=out_file, precision=6)
        assert os.path.exists(out_file)
        read_back = gpd.read_file(out_file)
        assert len(read_back) == 1
        assert read_back["name"].iloc[0] == "Export St"
        assert set(read_back.columns) == {
            "name",
            "separation_level",
            "street_classification",
            "maxspeed_int",
            "geometry",
        }
