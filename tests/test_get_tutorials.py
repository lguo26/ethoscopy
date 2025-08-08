"""
Unit tests for get_tutorials.py module.

Tests the tutorial data loading functionality.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from ethoscopy.misc.get_tutorials import get_tutorial


class TestGetTutorial:
    """Test cases for get_tutorial function."""

    @pytest.mark.unit
    def test_get_tutorial_overview_success(self):
        """Test successful loading of overview tutorial data."""
        data, meta = get_tutorial("overview")

        # Check that both data and metadata are DataFrames
        assert isinstance(data, pd.DataFrame)
        assert isinstance(meta, pd.DataFrame)

        # Check that data is not empty
        assert not data.empty
        assert not meta.empty

    @pytest.mark.unit
    def test_get_tutorial_circadian_success(self):
        """Test successful loading of circadian tutorial data."""
        data, meta = get_tutorial("circadian")

        # Check that both data and metadata are DataFrames
        assert isinstance(data, pd.DataFrame)
        assert isinstance(meta, pd.DataFrame)

        # Check that data is not empty
        assert not data.empty
        assert not meta.empty

    @pytest.mark.unit
    def test_get_tutorial_case_insensitive(self):
        """Test that data_type parameter is case insensitive."""
        # Test uppercase
        data1, meta1 = get_tutorial("OVERVIEW")
        assert isinstance(data1, pd.DataFrame)
        assert isinstance(meta1, pd.DataFrame)

        # Test mixed case
        data2, meta2 = get_tutorial("Circadian")
        assert isinstance(data2, pd.DataFrame)
        assert isinstance(meta2, pd.DataFrame)

    @pytest.mark.unit
    def test_get_tutorial_invalid_data_type(self):
        """Test error handling for invalid data_type."""
        with pytest.raises(KeyError, match="data_type must be one of"):
            get_tutorial("invalid")

    @pytest.mark.unit
    def test_get_tutorial_empty_string(self):
        """Test error handling for empty string data_type."""
        with pytest.raises(KeyError, match="data_type must be one of"):
            get_tutorial("")

    @pytest.mark.unit
    def test_get_tutorial_none_data_type(self):
        """Test error handling for None data_type."""
        with pytest.raises(AttributeError):
            get_tutorial(None)

    @pytest.mark.unit
    @patch("pandas.read_pickle")
    def test_get_tutorial_file_not_found(self, mock_read_pickle):
        """Test error handling when tutorial data files are missing."""
        mock_read_pickle.side_effect = FileNotFoundError("File not found")

        with pytest.raises(FileNotFoundError, match="Tutorial data files not found"):
            get_tutorial("overview")

    @pytest.mark.unit
    @patch("pandas.read_pickle")
    def test_get_tutorial_path_construction(self, mock_read_pickle):
        """Test that correct file paths are constructed."""
        mock_data = pd.DataFrame({"test": [1, 2, 3]})
        mock_meta = pd.DataFrame({"id": [1, 2, 3]})
        mock_read_pickle.return_value = mock_data

        get_tutorial("overview")

        # Check that read_pickle was called twice (once for data, once for meta)
        assert mock_read_pickle.call_count == 2

        # Check the file paths constructed
        calls = mock_read_pickle.call_args_list
        data_path = calls[0][0][0]
        meta_path = calls[1][0][0]

        # Verify paths end with expected filenames
        assert str(data_path).endswith("overview_data.pkl")
        assert str(meta_path).endswith("overview_meta.pkl")

    @pytest.mark.unit
    def test_get_tutorial_return_tuple(self):
        """Test that function returns a tuple of exactly 2 DataFrames."""
        result = get_tutorial("overview")

        # Check it's a tuple with exactly 2 elements
        assert isinstance(result, tuple)
        assert len(result) == 2

        data, meta = result
        assert isinstance(data, pd.DataFrame)
        assert isinstance(meta, pd.DataFrame)

    @pytest.mark.unit
    @patch("pathlib.Path.absolute")
    def test_get_tutorial_path_resolution(self, mock_absolute):
        """Test that absolute paths are properly resolved."""
        mock_path = MagicMock()
        mock_path.parent = Path("/fake/path/tutorial_data").parent
        mock_absolute.return_value = mock_path

        # This should not raise an exception even with mocked paths
        try:
            get_tutorial("overview")
        except FileNotFoundError:
            # Expected when using fake paths
            pass

        # Verify absolute() was called to resolve symlinks
        mock_absolute.assert_called_once()
