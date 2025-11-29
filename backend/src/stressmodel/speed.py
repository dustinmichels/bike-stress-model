from typing import List, Union

import numpy as np

SpeedInput = Union[str, float, List[str]]

DEFAULT_SPEED_LIMIT = None  # Global default speed limit in mph

SPEED_RANKINGS = [
    (20, 10),  # <= 20 mph -> 10 points
    (25, 8),  # <= 25 mph -> 8 points
    (30, 5),  # <= 30 mph -> 5 points
    (40, 3),  # <= 40 mph -> 3 points
    (50, 2),  # <= 50 mph -> 2 points
    (float("inf"), 1),  # > 50 mph -> 1 point
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


def get_speed_score(mph: float, rankings=SPEED_RANKINGS) -> int:
    """Get score based on speed."""
    # if np.isnan(mph):
    #     mph = DEFAULT_SPEED_LIMIT  # Use default when missing
    for threshold, score in rankings:
        if mph <= threshold:
            return score
    return rankings[-1][1]  # fallback


def run(df):
    """
    Process the DataFrame to extract maxspeed as integer.
    Missing speed limits default to 25 mph.

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

    # apply default for missing values
    if DEFAULT_SPEED_LIMIT is not None:
        df["maxspeed_int"] = (
            df["maxspeed_int"].fillna(DEFAULT_SPEED_LIMIT).astype("Int64")
        )

    df["maxspeed_int_score"] = df["maxspeed_int"].apply(get_speed_score)

    # return maxspeed and score series
    return df["maxspeed_int"], df["maxspeed_int_score"]
