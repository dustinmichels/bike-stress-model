"""
What type of cycleway is it?
"""

import numpy as np
import pandas as pd

RANKING = {
    "none": 0,
    "shared_lane": 2,  # in traffic
    "share_busway": 5,  # shared with bus
    "lane": 7,  # dedicated bike lane, not separate
    "lane_buffered": 7.5,  # Added buffered lane type
    "track": 8,  # totally separated (but sometimes used for lane with buffer)
    "separate": 10,  # totally separated
}


def combine_cycleways(row):
    """Accumulate all cycleway values into a single list."""

    cols = ["cycleway", "cycleway:both", "cycleway:left", "cycleway:right"]

    values = []
    for col in cols:
        v = row[col]

        # Normalize: listify arrays
        if isinstance(v, np.ndarray):
            v = v.tolist()

        # if missing, mark as "none"
        if v is None or v == "no":
            v = "none"
        if isinstance(v, float) and pd.isna(v):
            v = "none"

        # Handle lists
        if isinstance(v, list):
            values.extend(v)
        else:
            values.append(v)

    return values


def pick_best(values):
    return max(values, key=lambda v: RANKING.get(v, 0), default=None)


def apply_buffer_to_list(values, row):
    """Upgrade 'lane' to 'lane_buffered' in a list if buffer exists."""
    buffer_val = row.get("cycleway:buffer")
    if buffer_val is None:
        buffer_val = row.get("cycleway:separation")

    # Check if buffer exists and is valid
    has_buffer = (
        buffer_val is not None
        and buffer_val != "no"
        and not (isinstance(buffer_val, float) and pd.isna(buffer_val))
    )

    if not has_buffer:
        return values

    # Upgrade any 'lane' to 'lane_buffered'
    return ["lane_buffered" if v == "lane" else v for v in values]


def adjust_track_with_separation(row):
    """
    If cycleway is 'track' but separation is 'flex_post' or 'parking_lane', rename to 'lane_buffered'.
    """
    cycleway_all = row["cycleway_all"]
    separation = row.get("cycleway:separation")

    if "track" in cycleway_all and separation in ["flex_post", "parking_lane"]:
        # Replace 'track' with 'lane_buffered'
        cycleway_all = ["lane_buffered" if v == "track" else v for v in cycleway_all]
    return cycleway_all


def run(df):
    """
    Determine the separation level of cycling infrastructure for each row in the DataFrame.

    Args:
        df : pd.DataFrame
            DataFrame containing OSM edge data with cycleway-related columns.
    Returns:
        Tuple[pd.Series, pd.Series]

    About:
    ------
    "separation_level" : pd.Series
        "none"            : no cycling infrastructure
        "shared_lane"     : shared lane in traffic
        "share_busway"    : shared with bus
        "lane"            : dedicated bike lane, not separate
        "lane_buffered"   : dedicated bike lane with buffer
        "track"           : totally separated (but sometimes used for lane with buffer)
        "separate"        : totally separated

    "separation_score" : pd.Series
        Numerical score for separation level, higher is better

    """
    # make a copy
    df = df.copy()

    # combine all vals from cycleway tags into a single list
    df["cycleway_all"] = df.apply(combine_cycleways, axis=1)

    # rename: if buffer exists, rename 'lane' to 'lane_buffered'
    df["cycleway_all"] = df.apply(
        lambda row: apply_buffer_to_list(row["cycleway_all"], row), axis=1
    )

    # rename: if cycleway="track" but cycleway:separation="flex_post," rename to "lane_buffered"
    df["cycleway_all"] = df.apply(adjust_track_with_separation, axis=1)

    # pick best of list
    df["separation_level"] = df["cycleway_all"].apply(pick_best)

    # overwrite other vals:
    # check if highway=cycleway OR highway=path + bicycle=designated
    # if so, set cycleway_type to 'separate'
    is_cycleway = (df["highway"] == "cycleway") | (
        (df["highway"] == "path") & (df["bicycle"] == "designated")
    )
    df.loc[is_cycleway, "separation_level"] = "separate"

    # apply score column
    df["separation_score"] = df["separation_level"].apply(lambda v: RANKING.get(v, 0))

    # return separation level and score pd.Series
    return df["separation_level"], df["separation_score"]
