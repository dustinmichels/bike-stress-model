import numpy as np
import pandas as pd

from src.stressmodel import classification, speed


def _speeds(highway: list, maxspeed: list, default_mph: float) -> pd.Series:
    df = pd.DataFrame({"highway": highway, "maxspeed": maxspeed})
    street_classification, _ = classification.run(df)
    maxspeed_int, _ = speed.run(df, default_mph, street_classification)
    return maxspeed_int


def test_speed_default_covers_all_residential_class_edges():
    result = _speeds(
        highway=["residential", "service", ["service", "residential"], "primary"],
        maxspeed=[np.nan, np.nan, np.nan, np.nan],
        default_mph=25,
    )
    assert result.iloc[:3].tolist() == [25, 25, 25]
    assert np.isnan(result.iloc[3])


def test_speed_default_does_not_override_posted_speed():
    result = _speeds(highway=["residential"], maxspeed=["30 mph"], default_mph=20)
    assert result.tolist() == [30]
