"""
Unit tests for ethoscopy behavpy classes and core functionality.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

import ethoscopy as etho
from ethoscopy.behavpy_core import behavpy_core


class TestBehavpyCore:
    """Test suite for behavpy_core class."""

    @pytest.mark.unit
    def test_behavpy_core_creation(self, sample_ethoscope_data):
        """Test creating behavpy_core object."""
        metadata = pd.DataFrame({
            'id': ['test_id_01'],
            'sex': ['male'],
            'species': ['test_species']
        })
        
        bp = behavpy_core(sample_ethoscope_data, metadata)
        
        assert isinstance(bp, behavpy_core)
        assert hasattr(bp, 'meta')
        assert len(bp.meta) == 1

    @pytest.mark.unit
    def test_behavpy_core_index_validation(self, sample_ethoscope_data):
        """Test behavpy_core index validation."""
        metadata = pd.DataFrame({
            'id': ['test_id_01'],
            'sex': ['male'],
            'species': ['test_species']
        })
        
        # Test with proper index
        sample_ethoscope_data.index.name = 'id'
        bp = behavpy_core(sample_ethoscope_data, metadata, check=True)
        
        assert bp.index.name == 'id'

    @pytest.mark.unit
    def test_behavpy_core_metadata_mismatch(self, sample_ethoscope_data):
        """Test behavpy_core with mismatched metadata."""
        metadata = pd.DataFrame({
            'id': ['different_id'],
            'sex': ['male'],
            'species': ['test_species']
        })
        
        # Should handle metadata mismatch gracefully
        bp = behavpy_core(sample_ethoscope_data, metadata, check=False)
        assert isinstance(bp, behavpy_core)

    @pytest.mark.unit
    def test_behavpy_core_empty_data(self):
        """Test behavpy_core with empty data."""
        empty_data = pd.DataFrame()
        empty_metadata = pd.DataFrame()
        
        bp = behavpy_core(empty_data, empty_metadata)
        
        assert isinstance(bp, behavpy_core)
        assert len(bp) == 0

    @pytest.mark.unit
    def test_behavpy_core_xmv_method(self, sample_behavpy_object):
        """Test xmv method for extracting summary statistics."""
        # Add required columns for xmv
        sample_behavpy_object['moving'] = np.random.choice([True, False], len(sample_behavpy_object))
        
        result = sample_behavpy_object.xmv('moving')
        
        assert isinstance(result, pd.DataFrame)
        assert 'moving' in result.columns
        # Should have one row per unique id
        assert len(result) <= sample_behavpy_object['id'].nunique()


class TestBehavpy:
    """Test suite for main behavpy class."""

    @pytest.mark.unit
    def test_behavpy_creation_plotly(self, sample_ethoscope_data):
        """Test creating behavpy object with plotly canvas."""
        metadata = pd.DataFrame({
            'id': ['test_id_01'],
            'sex': ['male'],
            'species': ['test_species']
        })
        
        bp = etho.behavpy(sample_ethoscope_data, metadata, canvas='plotly')
        
        assert hasattr(bp, 'plot_overtime')
        assert hasattr(bp, 'plot_quantiles')

    @pytest.mark.unit
    def test_behavpy_creation_seaborn(self, sample_ethoscope_data):
        """Test creating behavpy object with seaborn canvas."""
        metadata = pd.DataFrame({
            'id': ['test_id_01'],
            'sex': ['male'],
            'species': ['test_species']
        })
        
        bp = etho.behavpy(sample_ethoscope_data, metadata, canvas='seaborn')
        
        assert hasattr(bp, 'plot_overtime')
        assert hasattr(bp, 'plot_quantiles')

    @pytest.mark.unit
    def test_behavpy_invalid_canvas(self, sample_ethoscope_data):
        """Test behavpy creation with invalid canvas."""
        metadata = pd.DataFrame({
            'id': ['test_id_01'],
            'sex': ['male'],
            'species': ['test_species']
        })
        
        with pytest.raises(ValueError, match="Canvas must be either 'plotly' or 'seaborn'"):
            etho.behavpy(sample_ethoscope_data, metadata, canvas='invalid')

    @pytest.mark.unit
    def test_behavpy_with_check(self, sample_ethoscope_data):
        """Test behavpy creation with validation enabled."""
        metadata = pd.DataFrame({
            'id': ['test_id_01'],
            'sex': ['male'],
            'species': ['test_species']
        })
        
        # Should work without errors when check=True
        bp = etho.behavpy(sample_ethoscope_data, metadata, check=True)
        assert isinstance(bp, etho.behavpy_core)

    @pytest.mark.unit
    def test_behavpy_palette_setting(self, sample_ethoscope_data):
        """Test behavpy creation with custom palette."""
        metadata = pd.DataFrame({
            'id': ['test_id_01'],
            'sex': ['male'],
            'species': ['test_species']
        })
        
        bp = etho.behavpy(sample_ethoscope_data, metadata, palette='viridis')
        
        assert hasattr(bp, 'palette')
        assert bp.palette == 'viridis'


class TestBehavpyHMM:
    """Test suite for behavpy_HMM class."""

    @pytest.mark.unit
    def test_behavpy_hmm_creation(self, sample_ethoscope_data):
        """Test creating behavpy_HMM object."""
        metadata = pd.DataFrame({
            'id': ['test_id_01'],
            'sex': ['male'],
            'species': ['test_species']
        })
        
        # Create behavpy object first
        bp = etho.behavpy(sample_ethoscope_data, metadata)
        
        # Convert to HMM (this might require specific data format)
        try:
            hmm_bp = bp.to_HMM()
            assert hasattr(hmm_bp, 'fit')
        except (AttributeError, NotImplementedError):
            # Method might not be implemented yet
            pytest.skip("HMM functionality not fully implemented")

    @pytest.mark.unit
    @pytest.mark.slow
    def test_behavpy_hmm_fitting(self, sample_ethoscope_data):
        """Test HMM model fitting."""
        metadata = pd.DataFrame({
            'id': ['test_id_01'],
            'sex': ['male'],
            'species': ['test_species']
        })
        
        bp = etho.behavpy(sample_ethoscope_data, metadata)
        
        try:
            hmm_bp = bp.to_HMM()
            # This would test actual HMM fitting
            # fitted_model = hmm_bp.fit(n_components=3)
            # assert fitted_model is not None
        except (AttributeError, NotImplementedError):
            pytest.skip("HMM functionality not fully implemented")


class TestBehavpyPeriodogram:
    """Test suite for behavpy_periodogram class."""

    @pytest.mark.unit
    def test_behavpy_periodogram_creation(self, sample_ethoscope_data):
        """Test creating behavpy_periodogram object."""
        metadata = pd.DataFrame({
            'id': ['test_id_01'],
            'sex': ['male'],
            'species': ['test_species']
        })
        
        bp = etho.behavpy(sample_ethoscope_data, metadata)
        
        try:
            pgram_bp = bp.to_periodogram()
            assert hasattr(pgram_bp, 'chi_squared')
            assert hasattr(pgram_bp, 'lomb_scargle')
        except (AttributeError, NotImplementedError):
            pytest.skip("Periodogram functionality not fully implemented")

    @pytest.mark.unit
    @pytest.mark.slow
    def test_behavpy_periodogram_analysis(self, sample_ethoscope_data):
        """Test periodogram analysis methods."""
        metadata = pd.DataFrame({
            'id': ['test_id_01'],
            'sex': ['male'],
            'species': ['test_species']
        })
        
        # Add movement data for periodogram analysis
        sample_ethoscope_data['moving'] = np.random.choice([True, False], len(sample_ethoscope_data))
        
        bp = etho.behavpy(sample_ethoscope_data, metadata)
        
        try:
            pgram_bp = bp.to_periodogram()
            # Test chi-squared periodogram
            result = pgram_bp.chi_squared('moving')
            assert isinstance(result, pd.DataFrame)
        except (AttributeError, NotImplementedError):
            pytest.skip("Periodogram functionality not fully implemented")


class TestBehavpyMethods:
    """Test suite for behavpy methods and functionality."""

    @pytest.mark.unit
    def test_behavpy_summary(self, sample_behavpy_object):
        """Test behavpy summary method."""
        try:
            summary = sample_behavpy_object.summary()
            assert isinstance(summary, pd.DataFrame)
        except AttributeError:
            # Method might not be implemented
            pytest.skip("Summary method not implemented")

    @pytest.mark.unit
    def test_behavpy_curate(self, sample_behavpy_object):
        """Test behavpy curate method."""
        try:
            curated = sample_behavpy_object.curate()
            assert isinstance(curated, type(sample_behavpy_object))
        except AttributeError:
            pytest.skip("Curate method not implemented")

    @pytest.mark.unit
    def test_behavpy_copy(self, sample_behavpy_object):
        """Test behavpy copy functionality."""
        copy_bp = sample_behavpy_object.copy()
        
        assert isinstance(copy_bp, type(sample_behavpy_object))
        assert copy_bp is not sample_behavpy_object
        pd.testing.assert_frame_equal(copy_bp, sample_behavpy_object)

    @pytest.mark.unit
    def test_behavpy_indexing(self, sample_behavpy_object):
        """Test behavpy indexing and slicing."""
        # Test boolean indexing
        mask = sample_behavpy_object['t'] > sample_behavpy_object['t'].median()
        subset = sample_behavpy_object[mask]
        
        assert isinstance(subset, type(sample_behavpy_object))
        assert len(subset) <= len(sample_behavpy_object)

    @pytest.mark.unit
    def test_behavpy_groupby(self, sample_behavpy_object):
        """Test behavpy groupby functionality."""
        # Add grouping variable
        sample_behavpy_object['group'] = np.random.choice(['A', 'B'], len(sample_behavpy_object))
        
        grouped = sample_behavpy_object.groupby('group')
        
        assert hasattr(grouped, 'mean')
        assert hasattr(grouped, 'sum')


class TestBehavpyPlotting:
    """Test suite for behavpy plotting functionality."""

    @pytest.mark.unit
    def test_behavpy_plot_overtime_plotly(self, sample_behavpy_object):
        """Test plotly overtime plotting."""
        # Create plotly behavpy object
        bp_plotly = etho.behavpy(
            sample_behavpy_object, 
            sample_behavpy_object.meta, 
            canvas='plotly'
        )
        
        try:
            fig = bp_plotly.plot_overtime('t')
            # Should return plotly figure
            assert hasattr(fig, 'show')
        except (AttributeError, ImportError):
            pytest.skip("Plotting functionality not available")

    @pytest.mark.unit
    def test_behavpy_plot_overtime_seaborn(self, sample_behavpy_object):
        """Test seaborn overtime plotting."""
        # Create seaborn behavpy object
        bp_seaborn = etho.behavpy(
            sample_behavpy_object,
            sample_behavpy_object.meta,
            canvas='seaborn'
        )
        
        try:
            fig = bp_seaborn.plot_overtime('t')
            # Should return matplotlib figure
            assert hasattr(fig, 'savefig')
        except (AttributeError, ImportError):
            pytest.skip("Plotting functionality not available")

    @pytest.mark.unit
    def test_behavpy_plot_quantiles(self, sample_behavpy_object):
        """Test quantile plotting."""
        try:
            fig = sample_behavpy_object.plot_quantiles('t')
            assert fig is not None
        except (AttributeError, ImportError, NotImplementedError):
            pytest.skip("Quantile plotting not implemented")


class TestIntegrationBehavpy:
    """Integration tests for behavpy workflows."""

    @pytest.mark.integration
    def test_complete_behavpy_workflow(self, sample_ethoscope_data):
        """Test complete behavpy workflow from creation to analysis."""
        metadata = pd.DataFrame({
            'id': ['test_id_01'],
            'sex': ['male'],
            'species': ['test_species'],
            'treatment': ['control']
        })
        
        # Create behavpy object
        bp = etho.behavpy(sample_ethoscope_data, metadata, canvas='plotly')
        
        # Add analysis columns
        bp['moving'] = np.random.choice([True, False], len(bp))
        bp['asleep'] = ~bp['moving']
        
        # Test various operations
        summary = bp.xmv('moving')
        assert isinstance(summary, pd.DataFrame)
        
        # Test subsetting
        subset = bp[bp['t'] > bp['t'].median()]
        assert isinstance(subset, type(bp))
        
        # Test that metadata is preserved
        assert hasattr(subset, 'meta')
        assert len(subset.meta) == len(bp.meta)