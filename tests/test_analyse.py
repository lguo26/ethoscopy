"""
Unit tests for ethoscopy.analyse module functions.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

from ethoscopy.analyse import (
    max_velocity_detector,
    sleep_annotation, 
    stimulus_response,
    cumsum_delta,
    prep_data_motion_detector,
    _find_runs
)


class TestMaxVelocityDetector:
    """Test suite for max_velocity_detector function."""

    @pytest.mark.unit
    def test_max_velocity_detector_success(self, sample_ethoscope_data):
        """Test successful velocity detection."""
        result = max_velocity_detector(sample_ethoscope_data)
        
        assert isinstance(result, pd.DataFrame)
        assert 'moving' in result.columns
        assert result['moving'].dtype == bool
        # Function bins data into 10-second windows, so output length should be duration/window_size
        expected_length = 3600 // 10  # 360 rows for 1 hour with 10s windows
        assert len(result) == expected_length

    @pytest.mark.unit
    def test_max_velocity_detector_custom_threshold(self, sample_ethoscope_data):
        """Test velocity detection with custom threshold."""
        result = max_velocity_detector(sample_ethoscope_data, velocity_correction_coef=0.01)
        
        assert isinstance(result, pd.DataFrame)
        assert 'moving' in result.columns

    @pytest.mark.unit
    def test_max_velocity_detector_empty_data(self):
        """Test velocity detection with empty data."""
        empty_data = pd.DataFrame(columns=['t', 'x', 'y', 'xy_dist_log10x1000'])
        
        result = max_velocity_detector(empty_data)
        
        # Empty data returns None (insufficient data for analysis)
        assert result is None

    @pytest.mark.unit
    def test_max_velocity_detector_missing_columns(self):
        """Test velocity detection with missing required columns."""
        # Create data with enough rows but missing required columns
        bad_data = pd.DataFrame({
            't': list(range(200)),
            'x': list(range(200))
            # Missing 'y' and 'xy_dist_log10x1000'
        })
        
        with pytest.raises(KeyError):
            max_velocity_detector(bad_data)


class TestSleepAnnotation:
    """Test suite for sleep_annotation function."""

    @pytest.mark.unit
    def test_sleep_annotation_success(self, sample_ethoscope_data):
        """Test successful sleep annotation."""
        # Add moving column (required for sleep annotation)
        sample_ethoscope_data['moving'] = np.random.choice([True, False], len(sample_ethoscope_data))
        
        result = sleep_annotation(sample_ethoscope_data)
        
        assert isinstance(result, pd.DataFrame)
        assert 'asleep' in result.columns
        assert result['asleep'].dtype == bool
        assert len(result) == len(sample_ethoscope_data)

    @pytest.mark.unit
    def test_sleep_annotation_custom_parameters(self, sample_ethoscope_data):
        """Test sleep annotation with custom parameters."""
        sample_ethoscope_data['moving'] = np.random.choice([True, False], len(sample_ethoscope_data))
        
        result = sleep_annotation(
            sample_ethoscope_data, 
            time_window_length=600,  # 10 minutes
            min_time_immobile=300    # 5 minutes
        )
        
        assert isinstance(result, pd.DataFrame)
        assert 'asleep' in result.columns

    @pytest.mark.unit
    def test_sleep_annotation_no_movement_data(self, sample_ethoscope_data):
        """Test sleep annotation without movement data."""
        with pytest.raises(KeyError):
            sleep_annotation(sample_ethoscope_data)  # No 'moving' column

    @pytest.mark.unit
    def test_sleep_annotation_all_moving(self, sample_ethoscope_data):
        """Test sleep annotation when animal is always moving."""
        sample_ethoscope_data['moving'] = True
        
        result = sleep_annotation(sample_ethoscope_data)
        
        assert isinstance(result, pd.DataFrame)
        assert 'asleep' in result.columns
        assert not result['asleep'].any()  # Should never be asleep

    @pytest.mark.unit
    def test_sleep_annotation_never_moving(self, sample_ethoscope_data):
        """Test sleep annotation when animal never moves."""
        sample_ethoscope_data['moving'] = False
        
        result = sleep_annotation(sample_ethoscope_data)
        
        assert isinstance(result, pd.DataFrame)
        assert 'asleep' in result.columns
        # Most points should be asleep (after initial delay)


class TestStimulusResponse:
    """Test suite for stimulus_response function."""

    @pytest.mark.unit
    def test_stimulus_response_success(self, sample_ethoscope_data):
        """Test successful stimulus response analysis."""
        # Create stimulus times
        stimulus_times = [600, 1200, 1800]  # 10, 20, 30 minutes
        
        result = stimulus_response(sample_ethoscope_data, stimulus_times)
        
        assert isinstance(result, pd.DataFrame)
        assert 'stimulus' in result.columns
        assert len(result) == len(sample_ethoscope_data)

    @pytest.mark.unit
    def test_stimulus_response_empty_stimuli(self, sample_ethoscope_data):
        """Test stimulus response with empty stimulus list."""
        result = stimulus_response(sample_ethoscope_data, [])
        
        assert isinstance(result, pd.DataFrame)
        assert 'stimulus' in result.columns
        assert not result['stimulus'].any()  # No stimuli should be marked

    @pytest.mark.unit
    def test_stimulus_response_custom_window(self, sample_ethoscope_data):
        """Test stimulus response with custom response window."""
        stimulus_times = [600]
        
        result = stimulus_response(
            sample_ethoscope_data, 
            stimulus_times,
            response_window=120  # 2 minutes
        )
        
        assert isinstance(result, pd.DataFrame)
        assert 'stimulus' in result.columns

    @pytest.mark.unit
    def test_stimulus_response_out_of_range_stimuli(self, sample_ethoscope_data):
        """Test stimulus response with stimuli outside data range."""
        # Stimuli before and after data range
        stimulus_times = [-100, 7200]  # Before start and after end
        
        result = stimulus_response(sample_ethoscope_data, stimulus_times)
        
        assert isinstance(result, pd.DataFrame)
        assert 'stimulus' in result.columns
        # Should handle gracefully without errors


class TestCumsumDelta:
    """Test suite for cumsum_delta function."""

    @pytest.mark.unit
    def test_cumsum_delta_success(self, sample_ethoscope_data):
        """Test successful cumulative delta calculation."""
        result = cumsum_delta(sample_ethoscope_data, 'xy_dist_log10x1000')
        
        assert isinstance(result, pd.DataFrame)
        assert 'xy_dist_log10x1000_cumdelta' in result.columns
        assert len(result) == len(sample_ethoscope_data)

    @pytest.mark.unit
    def test_cumsum_delta_custom_column_name(self, sample_ethoscope_data):
        """Test cumulative delta with custom column name."""
        result = cumsum_delta(sample_ethoscope_data, 'xy_dist_log10x1000', 'custom_cumdelta')
        
        assert isinstance(result, pd.DataFrame)
        assert 'custom_cumdelta' in result.columns

    @pytest.mark.unit
    def test_cumsum_delta_missing_column(self, sample_ethoscope_data):
        """Test cumulative delta with missing column."""
        with pytest.raises(KeyError):
            cumsum_delta(sample_ethoscope_data, 'nonexistent_column')

    @pytest.mark.unit
    def test_cumsum_delta_empty_data(self):
        """Test cumulative delta with empty data."""
        empty_data = pd.DataFrame(columns=['xy_dist_log10x1000'])
        
        result = cumsum_delta(empty_data, 'xy_dist_log10x1000')
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


class TestPrepDataMotionDetector:
    """Test suite for prep_data_motion_detector function."""

    @pytest.mark.unit
    def test_prep_data_motion_detector_success(self, sample_ethoscope_data):
        """Test successful motion detection data preparation."""
        result = prep_data_motion_detector(sample_ethoscope_data)
        
        assert isinstance(result, pd.DataFrame)
        assert 'xy_dist_log10x1000_cumdelta' in result.columns
        assert len(result) == len(sample_ethoscope_data)

    @pytest.mark.unit
    def test_prep_data_motion_detector_custom_column(self, sample_ethoscope_data):
        """Test motion detection prep with custom distance column."""
        # Add a custom distance column
        sample_ethoscope_data['custom_dist'] = sample_ethoscope_data['xy_dist_log10x1000'] * 2
        
        result = prep_data_motion_detector(sample_ethoscope_data, distance_col='custom_dist')
        
        assert isinstance(result, pd.DataFrame)
        assert 'custom_dist_cumdelta' in result.columns

    @pytest.mark.unit
    def test_prep_data_motion_detector_missing_distance_column(self, sample_ethoscope_data):
        """Test motion detection prep with missing distance column."""
        data_no_dist = sample_ethoscope_data.drop(columns=['xy_dist_log10x1000'])
        
        with pytest.raises(KeyError):
            prep_data_motion_detector(data_no_dist)


class TestFindRuns:
    """Test suite for _find_runs internal function."""

    @pytest.mark.unit
    def test_find_runs_basic(self):
        """Test basic run finding functionality."""
        mov = np.array([True, True, False, False, False, True, True])
        
        result = _find_runs(mov, 2)  # Minimum run length of 2
        
        assert isinstance(result, np.ndarray)
        assert len(result) == len(mov)
        assert result.dtype == bool

    @pytest.mark.unit
    def test_find_runs_no_valid_runs(self):
        """Test run finding when no runs meet minimum length."""
        mov = np.array([True, False, True, False, True])  # All runs length 1
        
        result = _find_runs(mov, 3)  # Minimum run length of 3
        
        assert isinstance(result, np.ndarray)
        assert not result.any()  # No runs should meet criteria

    @pytest.mark.unit
    def test_find_runs_all_same_value(self):
        """Test run finding with all same values."""
        mov = np.array([False] * 10)
        
        result = _find_runs(mov, 5)
        
        assert isinstance(result, np.ndarray)
        assert result.all()  # Should all be True (one long run)

    @pytest.mark.unit
    def test_find_runs_empty_array(self):
        """Test run finding with empty array."""
        mov = np.array([], dtype=bool)
        
        result = _find_runs(mov, 2)
        
        assert isinstance(result, np.ndarray)
        assert len(result) == 0


class TestIntegrationAnalysis:
    """Integration tests for analysis workflow."""

    @pytest.mark.integration
    def test_complete_analysis_pipeline(self, sample_ethoscope_data):
        """Test complete analysis pipeline from raw data to sleep annotation."""
        # Step 1: Detect movement
        data_with_movement = max_velocity_detector(sample_ethoscope_data)
        
        # Step 2: Annotate sleep
        data_with_sleep = sleep_annotation(data_with_movement)
        
        # Step 3: Add stimulus response
        stimulus_times = [600, 1200]
        final_data = stimulus_response(data_with_sleep, stimulus_times)
        
        # Verify final result
        assert isinstance(final_data, pd.DataFrame)
        assert 'moving' in final_data.columns
        assert 'asleep' in final_data.columns
        assert 'stimulus' in final_data.columns
        assert len(final_data) == len(sample_ethoscope_data)

    @pytest.mark.integration
    @pytest.mark.slow
    def test_analysis_with_large_dataset(self):
        """Test analysis functions with large dataset."""
        # Create larger dataset for performance testing
        n_points = 10000
        large_data = pd.DataFrame({
            't': np.linspace(0, 86400, n_points),  # 24 hours
            'x': np.random.normal(100, 20, n_points),
            'y': np.random.normal(100, 20, n_points),
            'xy_dist_log10x1000': np.random.exponential(100, n_points),
            'w': np.random.normal(10, 1, n_points),
            'h': np.random.normal(10, 1, n_points),
            'phi': np.random.uniform(0, 2*np.pi, n_points)
        })
        
        # Test that functions complete without error on large dataset
        result = max_velocity_detector(large_data)
        result = sleep_annotation(result)
        
        assert len(result) == n_points
        assert 'moving' in result.columns
        assert 'asleep' in result.columns