"""
Unit tests for get_tutorials.py module.

Tests the tutorial data loading functionality.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from ethoscopy.misc.get_tutorials import (
    ENV_OVERRIDE,
    TUTORIAL_DATA_FILES,
    TUTORIAL_DATA_URLS,
    _find_pickle,
    _search_paths,
    download_tutorial_data,
    get_tutorial,
    package_tutorial_data_dir,
    user_tutorial_data_dir,
)


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

        with pytest.raises(FileNotFoundError) as exc_info:
            get_tutorial("overview")

        msg = str(exc_info.value)
        # Must point users to the recovery path
        assert "download_tutorial_data" in msg
        assert "github" in msg.lower()

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

        # Verify absolute() was called to resolve symlinks (may be called
        # multiple times now because the search path is consulted twice — once
        # for the data pickle, once for the metadata pickle).
        mock_absolute.assert_called()


class TestDownloadTutorialData:
    """Test cases for download_tutorial_data()."""

    @pytest.mark.unit
    def test_urls_cover_expected_files(self):
        """Every advertised filename must have a URL pointing at the repo."""
        assert set(TUTORIAL_DATA_URLS) == set(TUTORIAL_DATA_FILES)
        for url in TUTORIAL_DATA_URLS.values():
            assert url.startswith("https://raw.githubusercontent.com/")
            assert "ethoscopy" in url
            assert "tutorial_data" in url

    @pytest.mark.unit
    def test_download_writes_every_file(self, tmp_path):
        """Each missing file should trigger one urlretrieve call."""
        with patch("ethoscopy.misc.get_tutorials.urlretrieve") as mock_fetch:
            # Simulate the download by creating an empty file at the destination.
            def fake_fetch(url, dest):
                Path(dest).write_bytes(b"")
                return dest, None

            mock_fetch.side_effect = fake_fetch

            out = download_tutorial_data(dest_dir=tmp_path, verbose=False)

        assert out == tmp_path
        assert mock_fetch.call_count == len(TUTORIAL_DATA_FILES)
        for name in TUTORIAL_DATA_FILES:
            assert (tmp_path / name).exists()

    @pytest.mark.unit
    def test_download_skips_existing_without_overwrite(self, tmp_path):
        """Pre-existing files should not be re-fetched unless overwrite=True."""
        # Pre-create half the files
        preexisting = TUTORIAL_DATA_FILES[:3]
        for name in preexisting:
            (tmp_path / name).write_bytes(b"already here")

        with patch("ethoscopy.misc.get_tutorials.urlretrieve") as mock_fetch:
            mock_fetch.side_effect = lambda url, dest: (
                Path(dest).write_bytes(b""),
                None,
            )
            download_tutorial_data(dest_dir=tmp_path, verbose=False)

        # Only the missing half should have been fetched
        assert mock_fetch.call_count == len(TUTORIAL_DATA_FILES) - len(preexisting)
        # Pre-existing content preserved
        for name in preexisting:
            assert (tmp_path / name).read_bytes() == b"already here"

    @pytest.mark.unit
    def test_download_overwrite_refetches_everything(self, tmp_path):
        """overwrite=True must re-fetch every file."""
        for name in TUTORIAL_DATA_FILES:
            (tmp_path / name).write_bytes(b"stale")

        with patch("ethoscopy.misc.get_tutorials.urlretrieve") as mock_fetch:
            mock_fetch.side_effect = lambda url, dest: (
                Path(dest).write_bytes(b"fresh"),
                None,
            )
            download_tutorial_data(dest_dir=tmp_path, overwrite=True, verbose=False)

        assert mock_fetch.call_count == len(TUTORIAL_DATA_FILES)
        for name in TUTORIAL_DATA_FILES:
            assert (tmp_path / name).read_bytes() == b"fresh"

    @pytest.mark.unit
    def test_download_network_error_is_wrapped(self, tmp_path):
        """A URLError from urlretrieve should surface a clear message."""
        from urllib.error import URLError

        with patch(
            "ethoscopy.misc.get_tutorials.urlretrieve",
            side_effect=URLError("no route to host"),
        ):
            with pytest.raises(URLError, match="Failed to download"):
                download_tutorial_data(dest_dir=tmp_path, verbose=False)

    @pytest.mark.unit
    def test_default_dest_is_user_cache(self, tmp_path, monkeypatch):
        """Calling download_tutorial_data() with no dest_dir uses the user cache."""
        # Redirect HOME so the "user cache" points somewhere disposable.
        monkeypatch.setenv("HOME", str(tmp_path))
        with patch("ethoscopy.misc.get_tutorials.urlretrieve") as mock_fetch:
            mock_fetch.side_effect = lambda url, dest: (
                Path(dest).write_bytes(b""),
                None,
            )
            out = download_tutorial_data(verbose=False)
        assert out == tmp_path / ".cache" / "ethoscopy" / "tutorial_data"
        assert out.is_dir()
        assert mock_fetch.call_count == len(TUTORIAL_DATA_FILES)

    @pytest.mark.unit
    def test_permission_error_is_wrapped(self, tmp_path, monkeypatch):
        """mkdir failures surface with a pointer to dest_dir / env override."""
        monkeypatch.setattr(
            Path,
            "mkdir",
            lambda self, *a, **kw: (_ for _ in ()).throw(PermissionError("ro")),
        )
        with pytest.raises(PermissionError, match="Cannot create tutorial data"):
            download_tutorial_data(dest_dir=tmp_path / "x", verbose=False)


class TestSearchPaths:
    """Exercise the multi-location lookup used by get_tutorial / get_HMM."""

    @pytest.mark.unit
    def test_search_paths_include_package_and_cache(self):
        paths = _search_paths()
        assert package_tutorial_data_dir() in paths
        assert user_tutorial_data_dir() in paths

    @pytest.mark.unit
    def test_env_override_is_inserted(self, tmp_path, monkeypatch):
        monkeypatch.setenv(ENV_OVERRIDE, str(tmp_path))
        paths = _search_paths()
        assert tmp_path in paths
        # Env override must come after the package dir but before the cache
        assert paths.index(tmp_path) < paths.index(user_tutorial_data_dir())

    @pytest.mark.unit
    def test_find_pickle_hits_env_override(self, tmp_path, monkeypatch):
        """_find_pickle should discover files placed in the env-override dir."""
        monkeypatch.setenv(ENV_OVERRIDE, str(tmp_path))
        # Shadow the package dir so the env-override dir wins.
        monkeypatch.setattr(
            "ethoscopy.misc.get_tutorials.package_tutorial_data_dir",
            lambda: tmp_path / "nonexistent_pkg_dir",
        )
        monkeypatch.setattr(
            "ethoscopy.misc.get_tutorials.user_tutorial_data_dir",
            lambda: tmp_path / "nonexistent_cache",
        )

        target = tmp_path / "overview_data.pkl"
        target.write_bytes(b"x")
        assert _find_pickle("overview_data.pkl") == target

    @pytest.mark.unit
    def test_find_pickle_returns_none_when_absent(self, tmp_path, monkeypatch):
        monkeypatch.delenv(ENV_OVERRIDE, raising=False)
        monkeypatch.setattr(
            "ethoscopy.misc.get_tutorials.package_tutorial_data_dir",
            lambda: tmp_path / "a",
        )
        monkeypatch.setattr(
            "ethoscopy.misc.get_tutorials.user_tutorial_data_dir",
            lambda: tmp_path / "b",
        )
        assert _find_pickle("overview_data.pkl") is None

    @pytest.mark.unit
    def test_get_tutorial_uses_cache_fallback(self, tmp_path, monkeypatch):
        """With pickles only in the cache dir, get_tutorial must still load them."""
        # Point the package dir at somewhere empty.
        monkeypatch.setattr(
            "ethoscopy.misc.get_tutorials.package_tutorial_data_dir",
            lambda: tmp_path / "empty_package",
        )
        # Point the cache dir at a populated fixture dir.
        cache = tmp_path / "cache"
        cache.mkdir()
        monkeypatch.setattr(
            "ethoscopy.misc.get_tutorials.user_tutorial_data_dir",
            lambda: cache,
        )
        # Copy real tutorial pickles in via a symlink to avoid duplicating ~31 MB
        # of bytes; only runs if the dev checkout actually has them on disk.
        real_pkg_dir = (
            Path(__file__).resolve().parents[1] / "src/ethoscopy/misc/tutorial_data"
        )
        if not (real_pkg_dir / "overview_data.pkl").is_file():
            pytest.skip("tutorial_data fixtures not present in this checkout")
        for name in ("overview_data.pkl", "overview_meta.pkl"):
            (cache / name).symlink_to(real_pkg_dir / name)

        data, meta = get_tutorial("overview")
        assert isinstance(data, pd.DataFrame) and not data.empty
        assert isinstance(meta, pd.DataFrame) and not meta.empty
