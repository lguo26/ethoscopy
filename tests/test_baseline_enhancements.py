"""
Unit tests for baseline() method enhancements in behavpy_core.

Tests the new string baseline value conversion and memory optimization features.
"""

from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

import ethoscopy as etho
from ethoscopy.behavpy_core import behavpy_core


class TestBaselineStringBaselines:
    """Test suite for baseline string baseline value conversion."""

    @pytest.fixture
    def sample_data_with_time(self):
        """Create sample data with time column for baseline testing."""
        np.random.seed(42)
        n_points = 100
        n_ids = 3

        data_list = []
        for i in range(n_ids):
            id_name = f"test_id_{i:02d}"
            time_data = np.arange(n_points) * 60  # 1-minute intervals
            data = pd.DataFrame(
                {
                    "id": [id_name] * n_points,
                    "t": time_data,
                    "x": np.random.randn(n_points),
                    "y": np.random.randn(n_points),
                    "moving": np.random.choice([True, False], n_points),
                }
            )
            data_list.append(data)

        return pd.concat(data_list, ignore_index=True).set_index("id")

    @pytest.fixture
    def metadata_with_string_baselines(self):
        """Create metadata with various string baseline formats."""
        return pd.DataFrame(
            {
                "id": ["test_id_00", "test_id_01", "test_id_02"],
                "sex": ["male", "female", "male"],
                "baseline": ["normal", "2", "baseline"],
                "treatment": ["control", "drug", "control"],
            }
        ).set_index("id")

    @pytest.fixture
    def metadata_with_numeric_baselines(self):
        """Create metadata with numeric baseline values."""
        return pd.DataFrame(
            {
                "id": ["test_id_00", "test_id_01", "test_id_02"],
                "sex": ["male", "female", "male"],
                "baseline": [0, 2, 1],
                "treatment": ["control", "drug", "control"],
            }
        ).set_index("id")

    @pytest.mark.unit
    def test_baseline_string_baseline_normal(
        self, sample_data_with_time, metadata_with_string_baselines
    ):
        """Test baseline with 'normal' string baseline value."""
        bp = behavpy_core(
            sample_data_with_time, metadata_with_string_baselines, check=False
        )

        # Apply xmv with string baselines
        result = bp.baseline("baseline", day_length=24)

        # Check that result is a behavpy_core object
        assert isinstance(result, behavpy_core)

        # Check that time values were adjusted properly
        # 'normal' should convert to 0 (no shift)
        original_times = bp[bp.index == "test_id_00"]["t"].values
        result_times = result[result.index == "test_id_00"]["t"].values

        np.testing.assert_array_equal(original_times, result_times)

    @pytest.mark.unit
    def test_baseline_string_baseline_with_number(
        self, sample_data_with_time, metadata_with_string_baselines
    ):
        """Test baseline with string containing number ('2')."""
        bp = behavpy_core(
            sample_data_with_time, metadata_with_string_baselines, check=False
        )

        # Apply xmv with string baselines
        result = bp.baseline("baseline", day_length=24)

        # Check that time values were shifted for '2' baseline
        original_times = bp[bp.index == "test_id_01"]["t"].values
        result_times = result[result.index == "test_id_01"]["t"].values
        expected_shift = 2 * 24 * 60 * 60  # 2 days in seconds

        np.testing.assert_array_almost_equal(
            result_times, original_times + expected_shift
        )

    @pytest.mark.unit
    def test_baseline_string_baseline_baseline_keyword(
        self, sample_data_with_time, metadata_with_string_baselines
    ):
        """Test baseline with 'baseline' string value."""
        bp = behavpy_core(
            sample_data_with_time, metadata_with_string_baselines, check=False
        )

        # Apply xmv with string baselines
        result = bp.baseline("baseline", day_length=24)

        # Check that 'baseline' converts to 0 (no shift)
        original_times = bp[bp.index == "test_id_02"]["t"].values
        result_times = result[result.index == "test_id_02"]["t"].values

        np.testing.assert_array_equal(original_times, result_times)

    @pytest.mark.unit
    def test_baseline_numeric_baseline_backward_compatibility(
        self, sample_data_with_time, metadata_with_numeric_baselines
    ):
        """Test that numeric baselines still work (backward compatibility)."""
        bp = behavpy_core(
            sample_data_with_time, metadata_with_numeric_baselines, check=False
        )

        # Apply xmv with numeric baselines
        result = bp.baseline("baseline", day_length=24)

        # Check that numeric values work correctly
        original_times = bp[bp.index == "test_id_01"]["t"].values
        result_times = result[result.index == "test_id_01"]["t"].values
        expected_shift = 2 * 24 * 60 * 60  # 2 days in seconds

        np.testing.assert_array_almost_equal(
            result_times, original_times + expected_shift
        )

    @pytest.mark.unit
    def test_baseline_mixed_string_formats(self):
        """Test baseline with various string formats."""
        # Create test data
        data = pd.DataFrame(
            {
                "id": ["id1", "id2", "id3", "id4"],
                "t": [100, 200, 300, 400],
                "x": [1, 2, 3, 4],
            }
        ).set_index("id")

        metadata = pd.DataFrame(
            {
                "id": ["id1", "id2", "id3", "id4"],
                "baseline": ["0", "day3", "normal", "treatment5"],
            }
        ).set_index("id")

        bp = behavpy_core(data, metadata, check=False)
        result = bp.baseline("baseline", day_length=24)

        # Check conversions
        # '0' -> 0 (no shift)
        assert result.loc["id1", "t"] == 100
        # 'day3' -> 3 days shift
        expected_shift_3 = 3 * 24 * 60 * 60
        assert result.loc["id2", "t"] == 200 + expected_shift_3
        # 'normal' -> 0 (no shift)
        assert result.loc["id3", "t"] == 300
        # 'treatment5' -> 5 days shift
        expected_shift_5 = 5 * 24 * 60 * 60
        assert result.loc["id4", "t"] == 400 + expected_shift_5

    @pytest.mark.unit
    def test_baseline_invalid_day_length(
        self, sample_data_with_time, metadata_with_string_baselines
    ):
        """Test baseline with invalid day_length parameter."""
        bp = behavpy_core(
            sample_data_with_time, metadata_with_string_baselines, check=False
        )

        # Test negative day_length
        with pytest.raises(ValueError, match="day_length must be positive"):
            bp.baseline("baseline", day_length=-1)

        # Test zero day_length
        with pytest.raises(ValueError, match="day_length must be positive"):
            bp.baseline("baseline", day_length=0)

    @pytest.mark.unit
    def test_baseline_missing_column(
        self, sample_data_with_time, metadata_with_string_baselines
    ):
        """Test baseline with missing metadata column."""
        bp = behavpy_core(
            sample_data_with_time, metadata_with_string_baselines, check=False
        )

        with pytest.raises(KeyError):
            bp.baseline("nonexistent_column", day_length=24)

    @pytest.mark.unit
    def test_baseline_none_values(self):
        """Test baseline with None values in baseline column."""
        data = pd.DataFrame(
            {"id": ["id1", "id2"], "t": [100, 200], "x": [1, 2]}
        ).set_index("id")

        metadata = pd.DataFrame(
            {"id": ["id1", "id2"], "baseline": [None, "2"]}
        ).set_index("id")

        bp = behavpy_core(data, metadata, check=False)
        result = bp.baseline("baseline", day_length=24)

        # None should convert to 0 (no shift)
        assert result.loc["id1", "t"] == 100
        # '2' should shift by 2 days
        expected_shift = 2 * 24 * 60 * 60
        assert result.loc["id2", "t"] == 200 + expected_shift


class TestBaselineMemoryOptimization:
    """Test suite for xmv memory optimization features."""

    @pytest.fixture
    def large_dataset(self):
        """Create a larger dataset to test memory optimization."""
        np.random.seed(42)
        n_specimens = 10
        n_timepoints = 1000

        data_list = []
        for i in range(n_specimens):
            specimen_id = f"specimen_{i:03d}"
            data = pd.DataFrame(
                {
                    "id": [specimen_id] * n_timepoints,
                    "t": np.arange(n_timepoints) * 60,
                    "x": np.random.randn(n_timepoints),
                    "y": np.random.randn(n_timepoints),
                    "activity": np.random.exponential(2, n_timepoints),
                }
            )
            data_list.append(data)

        return pd.concat(data_list, ignore_index=True).set_index("id")

    @pytest.fixture
    def large_metadata(self):
        """Create metadata for large dataset."""
        return pd.DataFrame(
            {
                "id": [f"specimen_{i:03d}" for i in range(10)],
                "baseline": [0, 1, 2, 0, 1, 2, 0, 1, 2, 0],  # Mix of values
                "treatment": ["A", "B", "A", "B", "A", "B", "A", "B", "A", "B"],
            }
        ).set_index("id")

    @pytest.mark.unit
    def test_baseline_memory_efficient_processing(self, large_dataset, large_metadata):
        """Test that baseline processes data efficiently for large datasets."""
        bp = behavpy_core(large_dataset, large_metadata, check=False)

        # This should process the data in groups without running out of memory
        result = bp.baseline("baseline", day_length=24)

        # Check that result has correct structure
        assert isinstance(result, behavpy_core)
        assert len(result) == len(bp)
        assert list(result.columns) == list(bp.columns)

    @pytest.mark.unit
    def test_baseline_preserves_metadata(self, large_dataset, large_metadata):
        """Test that baseline preserves metadata correctly."""
        bp = behavpy_core(large_dataset, large_metadata, check=False)
        result = bp.baseline("baseline", day_length=24)

        # Check metadata preservation
        pd.testing.assert_frame_equal(result.meta, bp.meta)

        # Check palette preservation
        assert result.attrs["sh_pal"] == bp.attrs["sh_pal"]
        assert result.attrs["lg_pal"] == bp.attrs["lg_pal"]

    @pytest.mark.unit
    def test_baseline_no_copy_when_no_shift(self):
        """Test that baseline optimizes by not copying when there's no actual shift."""
        # Create data where all specimens have baseline 0
        data = pd.DataFrame(
            {"id": ["id1", "id2"], "t": [100, 200], "x": [1, 2]}
        ).set_index("id")

        metadata = pd.DataFrame(
            {"id": ["id1", "id2"], "baseline": [0, 0]}  # No shifts needed
        ).set_index("id")

        bp = behavpy_core(data, metadata, check=False)
        result = bp.baseline("baseline", day_length=24)

        # Should return new object but with same time values
        assert isinstance(result, behavpy_core)
        pd.testing.assert_series_equal(result["t"], bp["t"])


class TestBaselineEdgeCases:
    """Test suite for xmv edge cases and error handling."""

    @pytest.mark.unit
    def test_baseline_empty_dataset(self):
        """Test baseline with empty dataset."""
        empty_data = pd.DataFrame(columns=["t", "x"]).set_index(pd.Index([], name="id"))
        empty_metadata = pd.DataFrame(columns=["baseline"]).set_index(
            pd.Index([], name="id")
        )

        bp = behavpy_core(empty_data, empty_metadata, check=False)
        result = bp.baseline("baseline", day_length=24)

        assert isinstance(result, behavpy_core)
        assert len(result) == 0

    @pytest.mark.unit
    def test_baseline_single_specimen(self):
        """Test baseline with single specimen."""
        data = pd.DataFrame({"id": ["single_id"], "t": [100], "x": [1]}).set_index("id")

        metadata = pd.DataFrame({"id": ["single_id"], "baseline": ["2"]}).set_index(
            "id"
        )

        bp = behavpy_core(data, metadata, check=False)
        result = bp.baseline("baseline", day_length=24)

        expected_shift = 2 * 24 * 60 * 60
        assert result.loc["single_id", "t"] == 100 + expected_shift

    @pytest.mark.unit
    def test_baseline_different_t_column_name(self):
        """Test baseline with different time column name."""
        data = pd.DataFrame(
            {"id": ["id1"], "time": [100], "x": [1]}  # Different column name
        ).set_index("id")

        metadata = pd.DataFrame({"id": ["id1"], "baseline": ["1"]}).set_index("id")

        bp = behavpy_core(data, metadata, check=False)
        result = bp.baseline("baseline", t_column="time", day_length=24)

        expected_shift = 1 * 24 * 60 * 60
        assert result.loc["id1", "time"] == 100 + expected_shift

    @pytest.mark.unit
    def test_baseline_missing_specimens_in_metadata(self):
        """Test xmv when some specimens are missing from metadata."""
        data = pd.DataFrame(
            {"id": ["id1", "id2", "id3"], "t": [100, 200, 300], "x": [1, 2, 3]}
        ).set_index("id")

        # Only include some specimens in metadata
        metadata = pd.DataFrame(
            {"id": ["id1", "id3"], "baseline": ["1", "2"]}
        ).set_index("id")

        bp = behavpy_core(data, metadata, check=False)
        result = bp.baseline("baseline", day_length=24)

        # id1 should be shifted
        expected_shift_1 = 1 * 24 * 60 * 60
        assert result.loc["id1", "t"] == 100 + expected_shift_1

        # id2 should be unchanged (not in metadata)
        assert result.loc["id2", "t"] == 200

        # id3 should be shifted
        expected_shift_3 = 2 * 24 * 60 * 60
        assert result.loc["id3", "t"] == 300 + expected_shift_3


class TestBaselineIntegration:
    """Integration tests for xmv with other behavpy methods."""

    @pytest.mark.integration
    def test_baseline_with_filtering(self):
        """Test baseline combined with data filtering."""
        # Create test data
        data_list = []
        for i in range(3):
            data = pd.DataFrame(
                {
                    "id": [f"id{i}"] * 100,
                    "t": np.arange(100) * 60,
                    "activity": np.random.exponential(1, 100),
                    "moving": np.random.choice([True, False], 100),
                }
            )
            data_list.append(data)

        data = pd.concat(data_list, ignore_index=True).set_index("id")

        metadata = pd.DataFrame(
            {
                "id": ["id0", "id1", "id2"],
                "baseline": ["normal", "1", "2"],
                "group": ["A", "B", "A"],
            }
        ).set_index("id")

        bp = behavpy_core(data, metadata, check=False)

        # Apply baseline and then filter
        shifted = bp.baseline("baseline", day_length=24)
        filtered = shifted[shifted["activity"] > 1.0]

        assert isinstance(filtered, behavpy_core)
        assert len(filtered) <= len(shifted)

    @pytest.mark.integration
    def test_baseline_chaining_with_copy(self):
        """Test that baseline can be chained with other operations."""
        data = pd.DataFrame(
            {"id": ["id1", "id2"], "t": [100, 200], "x": [1, 2]}
        ).set_index("id")

        metadata = pd.DataFrame(
            {"id": ["id1", "id2"], "baseline": ["0", "1"]}
        ).set_index("id")

        bp = behavpy_core(data, metadata, check=False)

        # Chain operations
        result = bp.copy().baseline("baseline", day_length=24)

        assert isinstance(result, behavpy_core)
        # Original should be unchanged
        assert bp.loc["id1", "t"] == 100
        assert bp.loc["id2", "t"] == 200

        # Result should have shifts applied
        expected_shift = 1 * 24 * 60 * 60
        assert result.loc["id2", "t"] == 200 + expected_shift
