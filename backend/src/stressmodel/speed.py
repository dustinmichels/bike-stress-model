from typing import List, Union

import numpy as np
import pandas as pd

SpeedInput = Union[str, float, List[str]]

DEFAULT_SPEED_LIMIT = None  # Global default speed limit in mph

SPEED_RANKINGS = [
    (20, 0),  # <= 20 mph -> 0 points
    (25, 1),  #
    (30, 2.5),  #
    (40, 3),  #
    (50, 3.5),  #
    (float("inf"), 4),  # > 50 mph -> 5 points
]


def extract_maxspeed(value: SpeedInput) -> float:
    """
    Extracts the maximum speed from a value.

    Args:
        value: A string like "25 mph", a float (np.nan), a list of strings.

    Returns:
        float or np.nan
    """

    def parse_speed(v: Union[str, float]) -> float:
        if isinstance(v, float):
            return v if not np.isnan(v) else np.nan
        if isinstance(v, str):
            try:
                return float(v.replace("mph", "").strip())
            except ValueError:
                return np.nan
        return np.nan

    if isinstance(value, list):
        speeds = [s for s in (parse_speed(v) for v in value) if not np.isnan(s)]
        return max(speeds) if speeds else np.nan

    return parse_speed(value)


def get_speed_score(mph: float, rankings=SPEED_RANKINGS) -> Union[int, float]:
    """Get score based on speed. Returns np.nan if mph is np.nan."""
    if pd.isna(mph):  # Handle both np.nan and pd.NA
        return np.nan

    for threshold, score in rankings:
        if mph <= threshold:
            return score
    return rankings[-1][1]  # fallback


def run(df):
    """
    Process the DataFrame to extract maxspeed as integer.
    Missing speed limits remain null unless DEFAULT_SPEED_LIMIT is set.

    Args:
        df: DataFrame with a 'maxspeed' column.
    Returns:
        Tuple[pd.Series, pd.Series]
        (maxspeed_int, maxspeed_int_score)
    """
    # make a copy
    df = df.copy()

    # extract maxspeed
    df["maxspeed_int"] = df["maxspeed"].apply(extract_maxspeed)

    # if "highway=residential" and maxspeed is missing, set to 20 mph
    mask_residential_missing = (df["highway"] == "residential") & (
        df["maxspeed_int"].isna()
    )
    df.loc[mask_residential_missing, "maxspeed_int"] = 20

    # apply default for missing values (if configured)
    if DEFAULT_SPEED_LIMIT is not None:
        df["maxspeed_int"] = (
            df["maxspeed_int"].fillna(DEFAULT_SPEED_LIMIT).astype("Int64")
        )

    # calculate score (will be np.nan when maxspeed_int is np.nan)
    df["maxspeed_int_score"] = df["maxspeed_int"].apply(get_speed_score)

    # return maxspeed and score series
    return df["maxspeed_int"], df["maxspeed_int_score"]
