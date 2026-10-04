import numpy as np
import pandas as pd

from src.stressmodel.scoring import Tier, Tiers

SpeedInput = str | float | list[str]

SPEED_TIERS = Tiers(
    (
        Tier(max_value=20, score=0),
        Tier(max_value=25, score=1),
        Tier(max_value=30, score=2.5),
        Tier(max_value=40, score=3),
        Tier(max_value=50, score=3.5),
        Tier(max_value=float("inf"), score=4),  # > 50 mph
    )
)


def extract_maxspeed(value: SpeedInput) -> float:
    """
    Extracts the maximum speed from a value.

    Args:
        value: A string like "25 mph", a float (np.nan), a list of strings.

    Returns:
        float or np.nan
    """

    def parse_speed(v: str | float) -> float:
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


def get_speed_score(mph: float) -> int | float:
    """Get score based on speed. Returns np.nan if mph is np.nan."""
    if pd.isna(mph):  # Handle both np.nan and pd.NA
        return np.nan
    return SPEED_TIERS.score(mph)


def run(
    df: pd.DataFrame,
    residential_default_mph: float,
    street_classification: pd.Series,
) -> tuple[pd.Series, pd.Series]:
    """
    Extract the posted speed in mph and score it.

    Residential-class edges (see `classification.run`) with no posted speed get
    the city's residential default. Other missing speeds stay null.

    Args:
        df: DataFrame with a 'maxspeed' column.
        residential_default_mph: Statutory default for the city's residential streets.
        street_classification: Output of `classification.run`, aligned with `df`.
    Returns:
        (maxspeed_int, maxspeed_int_score)
    """
    maxspeed_int = df["maxspeed"].apply(extract_maxspeed)
    missing_residential = maxspeed_int.isna() & (street_classification == "residential")
    maxspeed_int = maxspeed_int.mask(missing_residential, residential_default_mph)
    return maxspeed_int, maxspeed_int.apply(get_speed_score)
