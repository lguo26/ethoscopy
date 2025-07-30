"""
Unit tests for ethoscopy.load module functions.
"""

import pytest
import pandas as pd
import numpy as np
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

from ethoscopy.load import (
    link_meta_index, 
    load_ethoscope, 
    read_single_roi,
    load_ethoscope_metadata
)


class TestLinkMetaIndex:
    """Test suite for link_meta_index function."""

    @pytest.mark.unit
    def test_link_meta_index_success(self, sample_metadata_csv, tmp_path):
        """Test successful metadata linking."""
        # Create expected directory structure
        machine_dir = tmp_path / "test_results" / "ETHOSCOPE_001" / "2025-01-01_12-00-00"
        machine_dir.mkdir(parents=True)
        
        # Create a dummy database file
        db_file = machine_dir / "test.db"
        db_file.write_text("dummy db content")
        
        # Test the function
        result = link_meta_index(str(sample_metadata_csv), str(tmp_path / "test_results"))
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert 'path' in result.columns
        assert 'file_size' in result.columns
        assert 'id' in result.columns

    @pytest.mark.unit
    def test_link_meta_index_no_files(self, sample_metadata_csv, tmp_path):
        """Test metadata linking when no database files exist."""
        with pytest.raises(RuntimeError, match="No Ethoscope data could be found"):
            link_meta_index(str(sample_metadata_csv), str(tmp_path))

    @pytest.mark.unit
    def test_link_meta_index_missing_metadata(self, tmp_path):
        """Test metadata linking with missing metadata file."""
        missing_file = tmp_path / "missing.csv"
        with pytest.raises(FileNotFoundError):
            link_meta_index(str(missing_file), str(tmp_path))

    @pytest.mark.unit
    def test_link_meta_index_missing_columns(self, tmp_path):
        """Test metadata linking with missing required columns."""
        # Create metadata CSV missing required columns
        bad_metadata = pd.DataFrame({
            'date': ['2025-01-01'],
            'machine_name': ['ETHOSCOPE_001']
            # Missing region_id
        })
        csv_path = tmp_path / "bad_metadata.csv"
        bad_metadata.to_csv(csv_path, index=False)
        
        with pytest.raises(KeyError):
            link_meta_index(str(csv_path), str(tmp_path))


class TestReadSingleRoi:
    """Test suite for read_single_roi function."""

    @pytest.mark.unit
    def test_read_single_roi_success(self, linked_metadata_sample):
        """Test successful single ROI reading."""
        file_info = linked_metadata_sample.iloc[0]
        
        result = read_single_roi(file_info)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert 't' in result.columns
        assert 'x' in result.columns
        assert 'y' in result.columns

    @pytest.mark.unit
    def test_read_single_roi_time_filtering(self, linked_metadata_sample):
        """Test ROI reading with time constraints."""
        file_info = linked_metadata_sample.iloc[0]
        
        # Test with time constraints
        result = read_single_roi(file_info, min_time=0, max_time=1800)  # 30 minutes
        
        assert isinstance(result, pd.DataFrame)
        if len(result) > 0:
            assert result['t'].max() <= 1800

    @pytest.mark.unit
    def test_read_single_roi_invalid_time_range(self, linked_metadata_sample):
        """Test ROI reading with invalid time range."""
        file_info = linked_metadata_sample.iloc[0]
        
        with pytest.raises(ValueError, match="min_time is larger than max_time"):
            read_single_roi(file_info, min_time=3600, max_time=1800)

    @pytest.mark.unit
    def test_read_single_roi_missing_roi(self, mock_sqlite_db, tmp_path):
        """Test ROI reading when requested ROI doesn't exist."""
        # Create file info for non-existent ROI
        file_info = pd.Series({
            'path': str(mock_sqlite_db),
            'region_id': 999,  # Non-existent ROI
            'machine_id': 'test',
            'date': '2025-01-01'
        })
        
        result = read_single_roi(file_info)
        assert result is None

    @pytest.mark.unit 
    def test_read_single_roi_with_cache(self, linked_metadata_sample, tmp_path):
        """Test ROI reading with caching."""
        file_info = linked_metadata_sample.iloc[0]
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        
        # First call should create cache
        result1 = read_single_roi(file_info, cache=str(cache_dir))
        
        # Second call should use cache
        result2 = read_single_roi(file_info, cache=str(cache_dir))
        
        assert isinstance(result1, pd.DataFrame)
        assert isinstance(result2, pd.DataFrame)
        pd.testing.assert_frame_equal(result1, result2)


class TestLoadEthoscope:
    """Test suite for load_ethoscope function."""

    @pytest.mark.unit
    def test_load_ethoscope_success(self, linked_metadata_sample):
        """Test successful ethoscope data loading."""
        result = load_ethoscope(linked_metadata_sample, verbose=False)
        
        assert isinstance(result, pd.DataFrame)
        assert 'id' in result.columns
        if len(result) > 0:
            assert result['id'].iloc[0] == linked_metadata_sample['id'].iloc[0]

    @pytest.mark.unit
    def test_load_ethoscope_with_function(self, linked_metadata_sample):
        """Test ethoscope loading with processing function."""
        def dummy_function(data):
            """Dummy processing function that adds a column."""
            data['processed'] = True
            return data
        
        result = load_ethoscope(linked_metadata_sample, FUN=dummy_function, verbose=False)
        
        if len(result) > 0:
            assert 'processed' in result.columns
            assert result['processed'].all() == True

    @pytest.mark.unit
    def test_load_ethoscope_function_returns_none(self, linked_metadata_sample):
        """Test ethoscope loading when processing function returns None."""
        def failing_function(data):
            """Function that returns None."""
            return None
        
        result = load_ethoscope(linked_metadata_sample, FUN=failing_function, verbose=False)
        
        # Should return empty DataFrame when all processing fails
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @pytest.mark.unit
    def test_load_ethoscope_time_constraints(self, linked_metadata_sample):
        """Test ethoscope loading with time constraints."""
        result = load_ethoscope(
            linked_metadata_sample, 
            min_time=0, 
            max_time=1,  # 1 hour
            verbose=False
        )
        
        assert isinstance(result, pd.DataFrame)
        if len(result) > 0:
            assert result['t'].max() <= 3600  # 1 hour in seconds

    @pytest.mark.unit
    def test_load_ethoscope_empty_metadata(self):
        """Test ethoscope loading with empty metadata."""
        empty_metadata = pd.DataFrame()
        
        result = load_ethoscope(empty_metadata, verbose=False)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @pytest.mark.unit
    def test_load_ethoscope_id_column_handling(self, linked_metadata_sample):
        """Test that load_ethoscope properly handles existing id columns."""
        # This tests the specific bug we fixed
        result = load_ethoscope(linked_metadata_sample, verbose=False)
        
        assert isinstance(result, pd.DataFrame)
        if len(result) > 0:
            assert 'id' in result.columns
            # Should not raise ValueError about duplicate id column


class TestLoadEthoscopeMetadata:
    """Test suite for load_ethoscope_metadata function."""

    @pytest.mark.unit
    def test_load_ethoscope_metadata_success(self, sample_metadata_csv):
        """Test successful metadata loading."""
        result = load_ethoscope_metadata(str(sample_metadata_csv))
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert 'machine_name' in result.columns
        assert 'date' in result.columns
        assert 'region_id' in result.columns

    @pytest.mark.unit
    def test_load_ethoscope_metadata_missing_file(self, tmp_path):
        """Test metadata loading with missing file."""
        missing_file = tmp_path / "missing.csv"
        
        with pytest.raises(FileNotFoundError):
            load_ethoscope_metadata(str(missing_file))

    @pytest.mark.unit
    def test_load_ethoscope_metadata_nan_values(self, tmp_path):
        """Test metadata loading with NaN values."""
        # Create metadata with NaN values
        bad_metadata = pd.DataFrame({
            'date': ['2025-01-01', np.nan],
            'machine_name': ['ETHOSCOPE_001', 'ETHOSCOPE_002'],
            'region_id': [1, 2]
        })
        csv_path = tmp_path / "nan_metadata.csv"
        bad_metadata.to_csv(csv_path, index=False)
        
        with pytest.raises(ValueError, match="metadata contains NaN values"):
            load_ethoscope_metadata(str(csv_path))


class TestIntegrationLoadWorkflow:
    """Integration tests for the complete loading workflow."""

    @pytest.mark.integration
    def test_complete_loading_workflow(self, sample_metadata_csv, tmp_path):
        """Test the complete workflow from metadata CSV to loaded data."""
        # Create directory structure and database
        machine_dir = tmp_path / "results" / "ETHOSCOPE_001" / "2025-01-01_12-00-00"
        machine_dir.mkdir(parents=True)
        
        # Create a proper SQLite database
        db_path = machine_dir / "test.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create minimal required tables
        cursor.execute('CREATE TABLE ROI_MAP (roi_idx INTEGER, x INTEGER, y INTEGER, w INTEGER, h INTEGER)')
        cursor.execute('INSERT INTO ROI_MAP VALUES (1, 0, 0, 100, 100), (2, 100, 0, 100, 100)')
        
        cursor.execute('CREATE TABLE VAR_MAP (var_name TEXT, functional_type TEXT, sql_data_type TEXT)')
        cursor.execute('INSERT INTO VAR_MAP VALUES ("xy_dist_log10x1000", "distance", "REAL")')
        
        cursor.execute('CREATE TABLE METADATA (field TEXT, value TEXT)')
        cursor.execute('INSERT INTO METADATA VALUES ("date_time", "1640995200")')
        
        # Create sample tracking data
        sample_data = pd.DataFrame({
            'id': [1] * 100,
            't': np.linspace(0, 3600, 100),
            'x': np.random.normal(50, 10, 100),
            'y': np.random.normal(50, 10, 100),
            'w': np.full(100, 10),
            'h': np.full(100, 10),
            'phi': np.random.uniform(0, 2*np.pi, 100),
            'xy_dist_log10x1000': np.random.exponential(100, 100),
            'is_inferred': np.zeros(100),
            'has_interacted': np.zeros(100)
        })
        
        sample_data.to_sql('ROI_1', conn, if_exists='replace', index=False)
        sample_data.to_sql('ROI_2', conn, if_exists='replace', index=False)
        
        conn.commit()
        conn.close()
        
        # Test the complete workflow
        linked_metadata = link_meta_index(str(sample_metadata_csv), str(tmp_path / "results"))
        final_data = load_ethoscope(linked_metadata, verbose=False)
        
        assert isinstance(final_data, pd.DataFrame)
        assert len(final_data) > 0
        assert 'id' in final_data.columns
        assert 't' in final_data.columns