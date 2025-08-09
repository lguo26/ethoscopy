"""
Simple unit tests for behavpy_core.py module.

Focuses on basic methods that can be easily tested to improve coverage.
"""

import numpy as np
import pandas as pd
import pytest

from ethoscopy.behavpy_core import behavpy_core


@pytest.fixture
def simple_behavpy_data():
    """Simple sample data for testing."""
    data = pd.DataFrame(
        {
            "t": [0, 60, 120, 180, 240, 300, 360, 420, 480, 540],
            "id": [1] * 5 + [2] * 5,
            "moving": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
            "x": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
            "y": [50, 51, 52, 53, 54, 55, 56, 57, 58, 59],
            "xy_dist_log10x1000": [100, 50, 150, 75, 200, 25, 175, 125, 300, 60],
        }
    ).set_index("id")

    return data


@pytest.fixture
def simple_metadata():
    """Simple metadata for testing."""
    return pd.DataFrame(
        {
            "id": [1, 2],
            "genotype": ["WT", "mutant"],
            "sex": ["M", "F"],
            "treatment": ["control", "drug"],
        }
    ).set_index("id")


@pytest.fixture
def simple_behavpy_object(simple_behavpy_data, simple_metadata):
    """Create simple behavpy_core object for testing."""
    return behavpy_core(simple_behavpy_data, simple_metadata)


class TestBehavpyCoreBasics:
    """Test basic behavpy_core functionality."""

    @pytest.mark.unit
    def test_initialization_basic(self, simple_behavpy_data, simple_metadata):
        """Test basic initialization works."""
        bp = behavpy_core(simple_behavpy_data, simple_metadata)

        assert isinstance(bp, behavpy_core)
        assert hasattr(bp, "meta")
        assert len(bp) == len(simple_behavpy_data)

    @pytest.mark.unit
    def test_display_method(self, simple_behavpy_object):
        """Test display method runs without error."""
        import sys
        from io import StringIO

        # Capture output
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            simple_behavpy_object.display()
            output = sys.stdout.getvalue()
            assert len(output) > 0
            assert "METADATA" in output
            assert "DATA" in output
        finally:
            sys.stdout = old_stdout

    @pytest.mark.unit
    def test_summary_basic(self, simple_behavpy_object):
        """Test summary method runs without error."""
        import sys
        from io import StringIO

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            simple_behavpy_object.summary()
            output = sys.stdout.getvalue()
            assert len(output) > 0
            assert "behavpy table" in output
        finally:
            sys.stdout = old_stdout

    @pytest.mark.unit
    def test_summary_detailed(self, simple_behavpy_object):
        """Test detailed summary method."""
        import sys
        from io import StringIO

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            simple_behavpy_object.summary(detailed=True)
            output = sys.stdout.getvalue()
            assert len(output) > 0
        finally:
            sys.stdout = old_stdout

    @pytest.mark.unit
    def test_xmv_basic(self, simple_behavpy_object):
        """Test xmv method with single value."""
        result = simple_behavpy_object.xmv("genotype", "WT")

        assert isinstance(result, behavpy_core)
        assert len(result) <= len(simple_behavpy_object)
        assert hasattr(result, "meta")

    @pytest.mark.unit
    def test_xmv_multiple_values(self, simple_behavpy_object):
        """Test xmv method with multiple values."""
        result = simple_behavpy_object.xmv("genotype", "WT", "mutant")

        assert isinstance(result, behavpy_core)
        assert len(result) == len(simple_behavpy_object)

    @pytest.mark.unit
    def test_remove_basic(self, simple_behavpy_object):
        """Test remove method."""
        initial_len = len(simple_behavpy_object)
        result = simple_behavpy_object.remove("genotype", "mutant")

        assert isinstance(result, behavpy_core)
        assert len(result) < initial_len
        assert hasattr(result, "meta")

    @pytest.mark.unit
    def test_add_day_phase_basic(self, simple_behavpy_object):
        """Test add_day_phase method."""
        result = simple_behavpy_object.copy()
        result.add_day_phase()  # inplace=True by default

        assert "phase" in result.columns
        assert "day" in result.columns
        assert result["phase"].dtype.name == "category"

    @pytest.mark.unit
    def test_add_day_phase_not_inplace(self, simple_behavpy_object):
        """Test add_day_phase method with inplace=False."""
        result = simple_behavpy_object.add_day_phase(inplace=False)

        assert isinstance(result, behavpy_core)
        assert "phase" in result.columns
        assert "day" in result.columns
        # Original should be unchanged
        assert "phase" not in simple_behavpy_object.columns


class TestBehavpyCoreValidation:
    """Test validation methods."""

    @pytest.mark.unit
    def test_check_conform_valid_data(self, simple_behavpy_object):
        """Test _check_conform with valid data."""
        # Should not raise exception
        behavpy_core._check_conform(simple_behavpy_object)

    @pytest.mark.unit
    def test_check_conform_no_metadata(self):
        """Test _check_conform with invalid metadata."""
        data = pd.DataFrame({"t": [1, 2], "id": [1, 2]}).set_index("id")
        data.meta = "not_a_dataframe"  # Invalid metadata

        with pytest.raises(TypeError, match="Metadata input is not a pandas dataframe"):
            behavpy_core._check_conform(data)

    @pytest.mark.unit
    def test_check_lists_method(self, simple_behavpy_object):
        """Test _check_lists method."""
        # Test with valid column
        f_arg, f_lab = simple_behavpy_object._check_lists("genotype", None, None)

        assert isinstance(f_arg, list)
        assert isinstance(f_lab, list)
        assert len(f_arg) == len(f_lab)
        assert "WT" in f_arg
        assert "mutant" in f_arg

    @pytest.mark.unit
    def test_check_lists_invalid_column(self, simple_behavpy_object):
        """Test _check_lists with invalid column."""
        with pytest.raises(KeyError, match='Column "invalid" is not a metadata column'):
            simple_behavpy_object._check_lists("invalid", None, None)

    @pytest.mark.unit
    def test_check_lists_mismatched_labels(self, simple_behavpy_object):
        """Test _check_lists with mismatched label length."""
        with pytest.raises(ValueError, match="facet labels don't match"):
            simple_behavpy_object._check_lists("genotype", ["WT"], ["label1", "label2"])


class TestBehavpyCoreAttributes:
    """Test class attributes and properties."""

    @pytest.mark.unit
    def test_metadata_attribute(self, simple_behavpy_object):
        """Test that _metadata attribute is set correctly."""
        assert hasattr(simple_behavpy_object, "_metadata")
        assert "meta" in simple_behavpy_object._metadata

    @pytest.mark.unit
    def test_canvas_attribute(self, simple_behavpy_object):
        """Test canvas attribute is None for behavpy_core."""
        assert hasattr(simple_behavpy_object, "canvas")
        assert simple_behavpy_object.canvas is None

    @pytest.mark.unit
    def test_hmm_attributes(self, simple_behavpy_object):
        """Test HMM-related attributes."""
        assert hasattr(simple_behavpy_object, "_hmm_colours")
        assert hasattr(simple_behavpy_object, "_hmm_labels")
        assert simple_behavpy_object._hmm_colours is None
        assert simple_behavpy_object._hmm_labels is None

    @pytest.mark.unit
    def test_constructor_property(self, simple_behavpy_object):
        """Test _constructor property."""
        constructor = simple_behavpy_object._constructor
        assert hasattr(constructor, "cls")
        assert constructor.cls == behavpy_core

    @pytest.mark.unit
    def test_attrs_initialization(self, simple_behavpy_data, simple_metadata):
        """Test attrs are set during initialization."""
        bp = behavpy_core(simple_behavpy_data, simple_metadata, palette=["red", "blue"])

        assert "sh_pal" in bp.attrs
        assert bp.attrs["sh_pal"] == ["red", "blue"]


class TestBehavpyCoreErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.unit
    def test_xmv_invalid_column(self, simple_behavpy_object):
        """Test xmv with invalid column."""
        with pytest.raises(
            KeyError, match='Column heading "invalid" is not in the metadata table'
        ):
            simple_behavpy_object.xmv("invalid", "value")

    @pytest.mark.unit
    def test_xmv_invalid_value(self, simple_behavpy_object):
        """Test xmv with invalid value."""
        with pytest.raises(
            KeyError, match='Metavariable "invalid" is not in the column'
        ):
            simple_behavpy_object.xmv("genotype", "invalid")

    @pytest.mark.unit
    def test_remove_invalid_column(self, simple_behavpy_object):
        """Test remove with invalid column."""
        with pytest.raises(KeyError):
            simple_behavpy_object.remove("invalid_column", "value")


class TestBehavpyCoreIntegration:
    """Integration tests."""

    @pytest.mark.integration
    def test_method_chaining(self, simple_behavpy_object):
        """Test that methods can be chained."""
        result = simple_behavpy_object.xmv("genotype", "WT", "mutant").add_day_phase(
            inplace=False
        )

        assert isinstance(result, behavpy_core)
        assert "phase" in result.columns
        assert hasattr(result, "meta")

    @pytest.mark.integration
    def test_metadata_preservation(self, simple_behavpy_object):
        """Test metadata is preserved through operations."""
        original_meta_cols = len(simple_behavpy_object.meta.columns)

        result = simple_behavpy_object.xmv("genotype", "WT")

        assert hasattr(result, "meta")
        assert len(result.meta.columns) >= original_meta_cols


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
# Test comment for hook validation
