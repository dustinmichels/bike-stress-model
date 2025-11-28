import re
from typing import List, Union

import numpy as np
import pandas as pd

FEET_TO_M = 0.3048

SpeedInput = Union[str, float, List[str]]


def extract_width(value) -> float:
    """
    Width could be in meters (default) or feet (using notation like 9' or 9'6").
    It could also be a list of widths; in that case, return the maximum width.

    Return numeric width in meters from OSM width tags.
    """

    # Handle list - get maximum width
    if isinstance(value, list):
        widths = []
        for item in value:
            width = _parse_single_width(item)
            if not np.isnan(width):
                widths.append(width)
        return max(widths) if widths else np.nan

    # Handle NaN/None
    if pd.isna(value):
        return np.nan

    # Handle single value
    return _parse_single_width(value)


def _parse_single_width(value):
    """Parse a single width value (helper function)."""
    if pd.isna(value):
        return np.nan

    # Convert to string and strip whitespace
    s = str(value).strip()

    # Feet notation like 9' or 9'6"
    if "'" in s:
        # Match feet and optional inches: 9'6" or just 9'
        match = re.match(r"(\d+(?:\.\d+)?)'(?:\s*(\d+(?:\.\d+)?)\")?", s)
        if match:
            feet = float(match.group(1))
            inches = float(match.group(2)) if match.group(2) else 0
            return (feet + inches / 12.0) * FEET_TO_M
        else:
            # Fallback: just extract the number before the '
            match = re.search(r"(\d+(?:\.\d+)?)", s)
            if match:
                return float(match.group()) * FEET_TO_M
            return np.nan

    # Standard numeric meters
    match = re.search(r"\d+(?:\.\d+)?", s)
    if match:
        return float(match.group())

    return np.nan


def first_if_list(series: pd.Series) -> pd.Series:
    """
    Converts any list in a pandas Series to its first element,
    leaves other values unchanged.

    Parameters
    ----------
    series : pd.Series
        The pandas Series to process.

    Returns
    -------
    pd.Series
        Series with lists replaced by their first element.


    Usage
    -----
    >>> edges['cycleway'] = first_if_list(edges['cycleway'])
    """
    return series.apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x)
