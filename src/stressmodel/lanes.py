import numpy as np
import pandas as pd

from src.stressmodel.scoring import Tier, Tiers

LanesInput = str | int | float | list[str] | None

LANES_TIERS = Tiers(
    (
        Tier(max_value=2, score=0),  # 1-2 lanes
        Tier(max_value=3, score=2),
        Tier(max_value=4, score=3),
        Tier(max_value=5, score=3.5),
        Tier(max_value=float("inf"), score=4),  # 6+ lanes
    )
)

DEFAULT_LANES = None  # Global default for missing lane values


def extract_lanes(value: LanesInput) -> float:
    """
    Extracts the maximum number of lanes from a value.

    Args:
        value: An integer, a string, a float (np.nan), or a list of strings.

    Returns:
        float or np.nan
    """

    def parse_lanes(v: str | float) -> float:
        if isinstance(v, int):
            return float(v)
        if isinstance(v, float):
            return v if not np.isnan(v) else np.nan
        if isinstance(v, str):
            try:
                return float(v.strip())
            except ValueError:
                return np.nan
        return np.nan

    if isinstance(value, list):
        lanes = [l for l in (parse_lanes(v) for v in value) if not np.isnan(l)]
        return float(max(lanes)) if lanes else np.nan

    if value is None:
        return np.nan

    return parse_lanes(value)


def get_lanes_score(num_lanes: float) -> int | float:
    """Get score based on number of lanes."""
    if np.isnan(num_lanes):
        return 0
    return LANES_TIERS.score(num_lanes)


def run(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """
    Process the DataFrame to extract lanes as integer.

    Args:
        df: DataFrame with a 'lanes' column.
    Returns:
        Tuple[pd.Series, pd.Series]
        (lanes_int, lanes_int_score)
    """
    # make a copy
    df = df.copy()

    # extract lanes
    df["lanes_int"] = df["lanes"].apply(extract_lanes).astype("Int64")

    # fill missing values with default
    if DEFAULT_LANES is not None:
        df["lanes_int"] = df["lanes_int"].fillna(DEFAULT_LANES).astype("Int64")

    # score
    df["lanes_int_score"] = df["lanes_int"].apply(get_lanes_score)

    # return lanes and score series
    return df["lanes_int"], df["lanes_int_score"]
