"""
Unit tests for compatibility classes.

Tests behavpy_HMM_class.py, behavpy_class.py, and behavpy_periodogram_class.py.
These are backward compatibility classes for pre-2.0 data loading.
"""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from ethoscopy.behavpy_class import behavpy
from ethoscopy.behavpy_HMM_class import behavpy_HMM
from ethoscopy.behavpy_periodogram_class import behavpy_periodogram


@pytest.fixture
def sample_data():
    """Sample data for testing compatibility classes."""
    data = pd.DataFrame(
        {
            "t": [1, 2, 3, 4, 5],
            "moving": [1, 0, 1, 0, 1],
            "x": [10, 15, 20, 25, 30],
            "y": [5, 8, 12, 16, 20],
            "id": [1, 1, 1, 1, 1],
        }
    )
    data = data.set_index("id")
    return data


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing compatibility classes."""
    meta = pd.DataFrame(
        {"id": [1], "genotype": ["WT"], "sex": ["M"], "treatment": ["control"]}
    )
    meta = meta.set_index("id")
    return meta


class TestBehavpyHMM:
    """Test cases for behavpy_HMM compatibility class."""

    @pytest.mark.unit
    def test_behavpy_hmm_initialization(self, sample_data, sample_metadata):
        """Test basic initialization of behavpy_HMM class."""
        hmm_obj = behavpy_HMM(sample_data, sample_metadata)

        # Check inheritance from behavpy_core
        assert hasattr(hmm_obj, "meta")
        assert hmm_obj.meta.equals(sample_metadata)

        # Check data content
        assert len(hmm_obj) == len(sample_data)
        assert list(hmm_obj.columns) == list(sample_data.columns)

    @pytest.mark.unit
    def test_behavpy_hmm_metadata_attribute(self, sample_data, sample_metadata):
        """Test that _metadata attribute is properly set."""
        hmm_obj = behavpy_HMM(sample_data, sample_metadata)

        assert hasattr(hmm_obj, "_metadata")
        assert "meta" in hmm_obj._metadata

    @pytest.mark.unit
    def test_behavpy_hmm_canvas_none(self, sample_data, sample_metadata):
        """Test that _canvas is None by default."""
        hmm_obj = behavpy_HMM(sample_data, sample_metadata)

        assert hmm_obj._canvas is None

    @pytest.mark.unit
    def test_behavpy_hmm_hmm_attributes(self, sample_data, sample_metadata):
        """Test HMM-specific attributes initialization."""
        hmm_obj = behavpy_HMM(sample_data, sample_metadata)

        assert hmm_obj._hmm_colours is None
        assert hmm_obj._hmm_labels is None

    @pytest.mark.unit
    def test_behavpy_hmm_with_palette(self, sample_data, sample_metadata):
        """Test initialization with palette parameters."""
        palette = ["red", "blue", "green"]
        long_palette = ["color1", "color2", "color3", "color4"]

        hmm_obj = behavpy_HMM(
            sample_data, sample_metadata, palette=palette, long_palette=long_palette
        )

        assert hmm_obj.attrs["sh_pal"] == palette
        assert hmm_obj.attrs["lg_pal"] == long_palette

    @pytest.mark.unit
    def test_behavpy_hmm_constructor_property(self, sample_data, sample_metadata):
        """Test _constructor property returns correct constructor."""
        hmm_obj = behavpy_HMM(sample_data, sample_metadata)
        constructor = hmm_obj._constructor

        assert hasattr(constructor, "cls")
        assert constructor.cls == behavpy_HMM

    @pytest.mark.unit
    def test_behavpy_hmm_internal_constructor(self, sample_data, sample_metadata):
        """Test internal constructor functionality."""
        hmm_obj = behavpy_HMM(sample_data, sample_metadata)
        constructor = hmm_obj._constructor

        # Test constructor call
        new_obj = constructor(sample_data, meta=sample_metadata)
        assert isinstance(new_obj, behavpy_HMM)


class TestBehavpy:
    """Test cases for behavpy compatibility class."""

    @pytest.mark.unit
    def test_behavpy_initialization(self, sample_data, sample_metadata):
        """Test basic initialization of behavpy class."""
        bp_obj = behavpy(sample_data, sample_metadata)

        assert hasattr(bp_obj, "meta")
        assert bp_obj.meta.equals(sample_metadata)
        assert len(bp_obj) == len(sample_data)

    @pytest.mark.unit
    def test_behavpy_metadata_attribute(self, sample_data, sample_metadata):
        """Test that _metadata attribute is properly set."""
        bp_obj = behavpy(sample_data, sample_metadata)

        assert hasattr(bp_obj, "_metadata")
        assert "meta" in bp_obj._metadata

    @pytest.mark.unit
    def test_behavpy_canvas_none(self, sample_data, sample_metadata):
        """Test that _canvas is None by default."""
        bp_obj = behavpy(sample_data, sample_metadata)

        assert bp_obj._canvas is None

    @pytest.mark.unit
    def test_behavpy_hmm_attributes(self, sample_data, sample_metadata):
        """Test HMM-related attributes initialization."""
        bp_obj = behavpy(sample_data, sample_metadata)

        assert bp_obj._hmm_colours is None
        assert bp_obj._hmm_labels is None

    @pytest.mark.unit
    def test_behavpy_with_all_parameters(self, sample_data, sample_metadata):
        """Test initialization with all optional parameters."""
        palette = ["red", "blue"]
        long_palette = ["color1", "color2", "color3"]

        bp_obj = behavpy(
            sample_data,
            sample_metadata,
            palette=palette,
            long_palette=long_palette,
            check=True,
            copy=True,
        )

        assert bp_obj.attrs["sh_pal"] == palette
        assert bp_obj.attrs["lg_pal"] == long_palette

    @pytest.mark.unit
    def test_behavpy_constructor_property(self, sample_data, sample_metadata):
        """Test _constructor property functionality."""
        bp_obj = behavpy(sample_data, sample_metadata)
        constructor = bp_obj._constructor

        assert hasattr(constructor, "cls")
        assert constructor.cls == behavpy


class TestBehavpyPeriodogram:
    """Test cases for behavpy_periodogram compatibility class."""

    @pytest.mark.unit
    def test_behavpy_periodogram_initialization(self, sample_data, sample_metadata):
        """Test basic initialization of behavpy_periodogram class."""
        per_obj = behavpy_periodogram(sample_data, sample_metadata)

        assert hasattr(per_obj, "meta")
        assert per_obj.meta.equals(sample_metadata)
        assert len(per_obj) == len(sample_data)

    @pytest.mark.unit
    def test_behavpy_periodogram_metadata_attribute(self, sample_data, sample_metadata):
        """Test that _metadata attribute is properly set."""
        per_obj = behavpy_periodogram(sample_data, sample_metadata)

        assert hasattr(per_obj, "_metadata")
        assert "meta" in per_obj._metadata

    @pytest.mark.unit
    def test_behavpy_periodogram_canvas_none(self, sample_data, sample_metadata):
        """Test that _canvas is None by default."""
        per_obj = behavpy_periodogram(sample_data, sample_metadata)

        assert per_obj._canvas is None

    @pytest.mark.unit
    def test_behavpy_periodogram_hmm_attributes(self, sample_data, sample_metadata):
        """Test HMM-related attributes initialization."""
        per_obj = behavpy_periodogram(sample_data, sample_metadata)

        assert per_obj._hmm_colours is None
        assert per_obj._hmm_labels is None

    @pytest.mark.unit
    def test_behavpy_periodogram_with_palette(self, sample_data, sample_metadata):
        """Test initialization with palette parameters."""
        palette = ["green", "yellow"]
        long_palette = ["c1", "c2", "c3", "c4", "c5"]

        per_obj = behavpy_periodogram(
            sample_data, sample_metadata, palette=palette, long_palette=long_palette
        )

        assert per_obj.attrs["sh_pal"] == palette
        assert per_obj.attrs["lg_pal"] == long_palette

    @pytest.mark.unit
    def test_behavpy_periodogram_constructor_property(
        self, sample_data, sample_metadata
    ):
        """Test _constructor property functionality."""
        per_obj = behavpy_periodogram(sample_data, sample_metadata)
        constructor = per_obj._constructor

        assert hasattr(constructor, "cls")
        assert constructor.cls == behavpy_periodogram


class TestCompatibilityClassesIntegration:
    """Integration tests for all compatibility classes."""

    @pytest.mark.integration
    def test_all_classes_inherit_from_behavpy_core(self, sample_data, sample_metadata):
        """Test that all compatibility classes inherit from behavpy_core."""
        hmm_obj = behavpy_HMM(sample_data, sample_metadata)
        bp_obj = behavpy(sample_data, sample_metadata)
        per_obj = behavpy_periodogram(sample_data, sample_metadata)

        # All should have the same basic DataFrame structure
        assert len(hmm_obj) == len(bp_obj) == len(per_obj)
        assert list(hmm_obj.columns) == list(bp_obj.columns) == list(per_obj.columns)

    @pytest.mark.integration
    def test_classes_maintain_data_integrity(self, sample_data, sample_metadata):
        """Test that data is preserved correctly across all classes."""
        classes = [behavpy_HMM, behavpy, behavpy_periodogram]

        for cls in classes:
            obj = cls(sample_data, sample_metadata)

            # Check data values are preserved
            pd.testing.assert_frame_equal(
                obj[sample_data.columns], sample_data, check_names=False
            )

            # Check metadata is preserved
            pd.testing.assert_frame_equal(obj.meta, sample_metadata)

    @pytest.mark.integration
    def test_copy_parameter_functionality(self, sample_data, sample_metadata):
        """Test copy parameter works for all classes."""
        classes = [behavpy_HMM, behavpy, behavpy_periodogram]

        for cls in classes:
            # Test with copy=True (default)
            obj1 = cls(sample_data, sample_metadata, copy=True)

            # Test with copy=False
            obj2 = cls(sample_data, sample_metadata, copy=False)

            # Both should have the same values
            pd.testing.assert_frame_equal(
                obj1[sample_data.columns], obj2[sample_data.columns], check_names=False
            )
