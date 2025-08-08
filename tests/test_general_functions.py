"""
Unit tests for general_functions.py module.

Tests the concat, bootstrap, and rle utility functions.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from ethoscopy.behavpy_core import behavpy_core
from ethoscopy.misc.general_functions import bootstrap, concat, rle


@pytest.fixture
def sample_behavpy_1():
    """First sample behavpy object for concatenation tests."""
    data = pd.DataFrame({"t": [1, 2, 3], "moving": [1, 0, 1], "id": [1, 1, 1]})
    data = data.set_index("id")

    meta = pd.DataFrame({"id": [1], "genotype": ["WT"]})
    meta = meta.set_index("id")

    bp = behavpy_core(data, meta)
    bp.attrs = {"sh_pal": ["red", "blue"], "lg_pal": ["color1", "color2", "color3"]}
    return bp


@pytest.fixture
def sample_behavpy_2():
    """Second sample behavpy object for concatenation tests."""
    data = pd.DataFrame({"t": [1, 2, 3], "moving": [0, 1, 0], "id": [2, 2, 2]})
    data = data.set_index("id")

    meta = pd.DataFrame({"id": [2], "genotype": ["mutant"]})
    meta = meta.set_index("id")

    return behavpy_core(data, meta)


class TestConcat:
    """Test cases for concat function."""

    @pytest.mark.unit
    def test_concat_two_objects(self, sample_behavpy_1, sample_behavpy_2):
        """Test concatenating two behavpy objects."""
        result = concat(sample_behavpy_1, sample_behavpy_2)

        # Check result is correct type
        assert isinstance(result, behavpy_core)

        # Check data is combined
        assert len(result) == len(sample_behavpy_1) + len(sample_behavpy_2)

        # Check metadata is combined
        assert len(result.meta) == len(sample_behavpy_1.meta) + len(
            sample_behavpy_2.meta
        )

    @pytest.mark.unit
    def test_concat_no_arguments(self):
        """Test concat with no arguments raises ValueError."""
        with pytest.raises(ValueError, match="At least one behavpy object required"):
            concat()


class TestBootstrap:
    """Test cases for bootstrap function."""

    @pytest.fixture
    def sample_data(self):
        """Sample data for bootstrap testing."""
        np.random.seed(42)  # For reproducible tests
        return np.random.normal(10, 2, 100)

    @pytest.mark.unit
    def test_bootstrap_basic(self, sample_data):
        """Test basic bootstrap functionality."""
        lower, upper = bootstrap(sample_data, n=100)

        # Check return types
        assert isinstance(lower, (float, np.floating))
        assert isinstance(upper, (float, np.floating))

        # Check that upper bound is higher than lower bound
        assert upper > lower

    @pytest.mark.unit
    def test_bootstrap_single_value(self):
        """Test bootstrap with single value."""
        single_value = np.array([5.0])
        lower, upper = bootstrap(single_value, n=100)

        # With single value, CI should be the same value
        assert lower == upper == 5.0


class TestRle:
    """Test cases for rle (run-length encoding) function."""

    @pytest.mark.unit
    def test_rle_basic(self):
        """Test basic RLE functionality."""
        data = np.array([1, 1, 1, 2, 2, 3, 3, 3, 3])
        values, starts, lengths = rle(data)

        # Check return types
        assert isinstance(values, np.ndarray)
        assert isinstance(starts, np.ndarray)
        assert isinstance(lengths, np.ndarray)

        # Check values
        np.testing.assert_array_equal(values, [1, 2, 3])
        np.testing.assert_array_equal(starts, [0, 3, 5])
        np.testing.assert_array_equal(lengths, [3, 2, 4])

    @pytest.mark.unit
    def test_rle_empty_array(self):
        """Test RLE with empty array."""
        data = np.array([])
        values, starts, lengths = rle(data)

        assert len(values) == 0
        assert len(starts) == 0
        assert len(lengths) == 0

    @pytest.mark.unit
    def test_rle_multidimensional_error(self):
        """Test RLE with multidimensional array raises error."""
        data = np.array([[1, 2], [3, 4]])

        with pytest.raises(ValueError, match="only 1D array supported"):
            rle(data)
