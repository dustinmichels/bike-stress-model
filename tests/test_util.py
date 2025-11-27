from typing import List, Union
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

# Assuming your main file is named network_processing.py
from util import (
    FEET_TO_M,
    extract_maxspeed,
    extract_width,
)


class TestExtractMaxspeed:
    """Test suite for extract_maxspeed function."""

    # Tests for string inputs
    def test_string_with_mph(self):
        """Test parsing a string with mph suffix."""
        assert extract_maxspeed("25 mph") == 25.0
        assert extract_maxspeed("50 mph") == 50.0

    def test_string_without_mph(self):
        """Test parsing a string without mph suffix."""
        assert extract_maxspeed("30") == 30.0
        assert extract_maxspeed("65") == 65.0

    def test_string_with_extra_whitespace(self):
        """Test parsing strings with extra whitespace."""
        assert extract_maxspeed("  25  mph  ") == 25.0
        assert extract_maxspeed("30mph") == 30.0

    def test_invalid_string(self):
        """Test parsing invalid string values."""
        assert np.isnan(extract_maxspeed("invalid"))
        assert np.isnan(extract_maxspeed("mph"))
        assert np.isnan(extract_maxspeed(""))
        assert np.isnan(extract_maxspeed("abc mph"))

    def test_nan_float(self):
        """Test NaN float input."""
        assert np.isnan(extract_maxspeed(np.nan))

    # Tests for list inputs
    def test_list_of_strings(self):
        """Test list of string values."""
        assert extract_maxspeed(["25 mph", "30 mph", "20 mph"]) == 30.0
        assert extract_maxspeed(["10", "20", "15"]) == 20.0

    def test_list_mixed_types(self):
        """Test list with mixed string and float values."""
        assert extract_maxspeed(["25 mph", 30.0, "20 mph"]) == 30.0
        assert extract_maxspeed([15.0, "25 mph", 20.0]) == 25.0

    def test_empty_list(self):
        """Test empty list input."""
        assert np.isnan(extract_maxspeed([]))


class TestExtractWidth:
    """Tests for extract_width function."""

    def test_simple_meters(self):
        assert extract_width("3.5") == 3.5
        assert extract_width("10") == 10.0

    def test_feet_only(self):
        result = extract_width("10'")
        expected = 10.0 * FEET_TO_M
        assert abs(result - expected) < 0.001

    def test_feet_and_inches(self):
        # 9'6" = 9.5 feet
        result = extract_width("9'6\"")
        expected = 9.5 * FEET_TO_M
        assert abs(result - expected) < 0.001

    def test_feet_with_decimals(self):
        result = extract_width("12.5'")
        expected = 12.5 * FEET_TO_M
        assert abs(result - expected) < 0.001

    def test_nan_input(self):
        assert pd.isna(extract_width(np.nan))
        assert pd.isna(extract_width(None))

    def test_no_numbers(self):
        assert pd.isna(extract_width("unknown"))

    def test_with_units_meters(self):
        assert extract_width("3.5 m") == 3.5
        assert extract_width("10m") == 10.0

    def test_list_input(self):
        # If width data can also be lists (similar to maxspeed)
        assert extract_width(["3.5", "4.0"]) in [3.5, 4.0]  # Depends on implementation

    def test_empty_string(self):
        assert pd.isna(extract_width(""))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
