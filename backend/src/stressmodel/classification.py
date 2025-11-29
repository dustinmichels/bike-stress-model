from typing import List, Union

import numpy as np
import pandas as pd

StreetInput = Union[str, List[str]]

# Street type classifications
# See: https://wiki.openstreetmap.org/wiki/Key:highway
STREET_CLASSIFICATIONS = {
    # Cycleway category - dedicated bike infrastructure and low-traffic paths
    "cycleway": "dedicated_path",
    "path": "dedicated_path",
    "pedestrian": "dedicated_path",
    "footway": "dedicated_path",
    "bridleway": "dedicated_path",
    "steps": "dedicated_path",  # Though not rideable, it's pedestrian infrastructure
    # Residential category - low-traffic local streets
    "residential": "residential",
    "living_street": "residential",
    "service": "residential",
    "unclassified": "residential",
    "track": "residential",
    # Medium-capacity category - connecting roads with moderate traffic
    "tertiary": "medium-capacity",
    "secondary": "medium-capacity",
    "secondary_link": "medium-capacity",
    "primary": "medium-capacity",
    "primary_link": "medium-capacity",
    # Motorway category - high-capacity roads
    "trunk": "motorway",
    "trunk_link": "motorway",
    "motorway": "motorway",
    "motorway_link": "motorway",
    "busway": "motorway",
}

# Scores for each classification (best to worst for cycling)
CLASSIFICATION_SCORES = {
    "dedicated_path": 10,
    "residential": 7,
    "medium-capacity": 3,
    "motorway": 0,
}

# Default classification for unknown types
DEFAULT_CLASSIFICATION = "medium-capacity"


def extract_street_type(value: StreetInput) -> str:
    """
    Extracts the street type from a value.

    Args:
        value: A string like "residential", a list of strings like ['path', 'service'].

    Returns:
        str representing the primary street type, or "" if unknown.
    """
    if isinstance(value, float) and np.isnan(value):
        return ""

    if isinstance(value, list):
        # If multiple types, prioritize the best one for cycling
        valid_types = [v for v in value if isinstance(v, str)]
        if not valid_types:
            return ""
        # Return the type with the highest classification score
        return max(
            valid_types,
            key=lambda x: CLASSIFICATION_SCORES.get(
                STREET_CLASSIFICATIONS.get(x, DEFAULT_CLASSIFICATION),
                CLASSIFICATION_SCORES[DEFAULT_CLASSIFICATION],
            ),
        )

    if isinstance(value, str):
        return value.strip()

    return ""


def get_street_classification(street_type: str) -> str:
    """Get classification based on street type."""
    if pd.isna(street_type):
        return np.nan
    return STREET_CLASSIFICATIONS.get(street_type, DEFAULT_CLASSIFICATION)


def get_street_score(classification: str) -> int:
    """Get score based on street classification."""
    if pd.isna(classification):
        return 0
    return CLASSIFICATION_SCORES.get(
        classification, CLASSIFICATION_SCORES[DEFAULT_CLASSIFICATION]
    )


def run(df):
    """
    Process the DataFrame to extract street classification and score.

    Args:
        df: DataFrame with a 'highway' column.
    Returns:
        Tuple[pd.Series, pd.Series]
        (street_classification, street_score)
    """
    # make a copy
    df = df.copy()

    # extract street type first
    df["street_type"] = df["highway"].apply(extract_street_type)

    # classify street type
    df["street_classification"] = df["street_type"].apply(get_street_classification)

    # get score from classification
    df["street_score"] = df["street_classification"].apply(get_street_score)

    # return classification and score series
    return df["street_classification"], df["street_score"]
