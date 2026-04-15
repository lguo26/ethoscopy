"""
Regression tests for ``load_ethoscope_metadata``.

These tests cover the edge cases that previously raised ``KeyError`` when
parsing hardware_info, and the renaming of the interactor kwarg
``date_range`` to ``stimulus_range``.

Issue: https://github.com/gilestrolab/ethoscopy/pull/6
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from ethoscopy.load import load_ethoscope_metadata


def _make_metadata_db(tmp_path, *, hardware_info, selected_options):
    """Build a minimal ethoscope .db file with a populated METADATA table.

    Args:
        tmp_path: pytest ``tmp_path`` fixture.
        hardware_info (str): Python-literal string stored in the hardware_info row.
        selected_options (str): Python-literal string stored in the selected_options row.

    Returns:
        pathlib.Path: Path to the new database.
    """
    db_path = tmp_path / "metadata_fixture.db"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("CREATE TABLE METADATA (field TEXT, value TEXT)")
        rows = [
            ("date_time", "1640995200"),  # 2022-01-01 00:00:00 UTC
            ("machine_id", "ETHOSCOPE_TEST_001"),
            ("machine_name", "ETHOSCOPE_TEST"),
            ("experimental_info", "{'code': 'EXP1', 'name': 'test'}"),
            ("hardware_info", hardware_info),
            ("selected_options", selected_options),
        ]
        conn.executemany("INSERT INTO METADATA VALUES (?, ?)", rows)
        conn.commit()
    finally:
        conn.close()
    return db_path


def _metadata_df(db_path):
    return pd.DataFrame(
        {
            "path": [str(db_path)],
            "machine_name": ["ETHOSCOPE_TEST"],
            "date": ["2022-01-01"],
        }
    )


# A plain interactor selected_options blob with no stimulus window.
_BASIC_SELECTED_OPTIONS = "{'interactor': {'class': 'DefaultInteractor', 'kwargs': {'velocity_correction_coef': 0.05}}}"

# An interactor blob carrying the legacy 'date_range' kwarg that we rename.
_SD_SELECTED_OPTIONS = (
    "{'interactor': {'class': 'SleepDepStimulator', "
    "'kwargs': {'velocity_correction_coef': 0.05, "
    "'date_range': '2022-01-01T09:00:00/2022-01-02T09:00:00'}}}"
)

# Newer firmwares wrap selected_options in an OrderedDict(...) call. The
# parser uses ``eval``, so the OrderedDict name must be importable from
# load.py's module globals for this to round-trip.
_ORDERED_DICT_SELECTED_OPTIONS = (
    "OrderedDict(["
    "('interactor', {'class': 'DefaultInteractor', "
    "'kwargs': {'velocity_correction_coef': 0.05}})"
    "])"
)


_REAL_HARDWARE_INFO = (
    "{'kernel': '6.1.14-1-rpi-ARCH', "
    "'pi_version': {'model_number': 3, 'model_type': 'Model B Plus Rev'}, "
    "'camera': {'IFD0.Model': 'RP_imx219', 'IFD0.Make': 'RaspberryPi', 'version': 'PINoIR 2'}, "
    "'SD_CARD_AGE': 20528213.03, "
    "'partitions': [{'Filesystem': '/dev/root'}], "
    "'SD_CARD_NAME': 'x.img'}"
)


class TestLoadEthoscopeMetadataFixes:
    """Regression tests for load_ethoscope_metadata."""

    @pytest.mark.unit
    def test_hardware_info_without_partitions(self, tmp_path):
        """pop('partitions') must not raise when the key is absent."""
        # Identical to real firmware output but with 'partitions' omitted.
        hardware_info = (
            "{'kernel': '6.1.14-1-rpi-ARCH', " "'camera': {'version': 'PINoIR 2'}}"
        )
        db = _make_metadata_db(
            tmp_path,
            hardware_info=hardware_info,
            selected_options=_BASIC_SELECTED_OPTIONS,
        )

        result = load_ethoscope_metadata(_metadata_df(db))

        assert len(result) == 1
        assert result.index.name == "machine_id"
        # 'camera' subsystem reported version 'PINoIR 2' — it propagates as the
        # value of the 'camera' column on the 'version' row.
        assert result.iloc[0]["camera"] == "PINoIR 2"

    @pytest.mark.unit
    def test_hardware_info_without_version_row(self, tmp_path):
        """No sub-dict carries a 'version' key → hdi falls back to empty."""
        # Every value is a scalar, so the transposed DataFrame has no
        # 'version' row. Historically this raised KeyError.
        hardware_info = (
            "{'kernel': '6.1.14-1-rpi-ARCH', "
            "'partitions': [1, 2], "
            "'SD_CARD_AGE': 1234.5}"
        )
        db = _make_metadata_db(
            tmp_path,
            hardware_info=hardware_info,
            selected_options=_BASIC_SELECTED_OPTIONS,
        )

        # Must not raise.
        result = load_ethoscope_metadata(_metadata_df(db))

        assert len(result) == 1
        # No hardware-version columns should have leaked in.
        assert "camera" not in result.columns or pd.isna(result.iloc[0].get("camera"))

    @pytest.mark.unit
    def test_hardware_info_realistic(self, tmp_path):
        """Happy path with a real-shaped hardware_info blob."""
        db = _make_metadata_db(
            tmp_path,
            hardware_info=_REAL_HARDWARE_INFO,
            selected_options=_BASIC_SELECTED_OPTIONS,
        )

        result = load_ethoscope_metadata(_metadata_df(db))

        assert result.iloc[0]["camera"] == "PINoIR 2"
        # Scalars in hardware_info are broadcast across the version row and
        # should appear alongside it.
        assert result.iloc[0]["kernel"] == "6.1.14-1-rpi-ARCH"

    @pytest.mark.unit
    def test_interactor_date_range_renamed_to_stimulus_range(self, tmp_path):
        """Interactor kwarg 'date_range' must be surfaced as 'stimulus_range'."""
        hardware_info = "{'version': {'id': 'abc'}}"
        db = _make_metadata_db(
            tmp_path,
            hardware_info=hardware_info,
            selected_options=_SD_SELECTED_OPTIONS,
        )

        result = load_ethoscope_metadata(_metadata_df(db))

        assert "stimulus_range" in result.columns
        assert "date_range" not in result.columns
        assert (
            result.iloc[0]["stimulus_range"]
            == "2022-01-01T09:00:00/2022-01-02T09:00:00"
        )

    @pytest.mark.unit
    def test_no_stimulus_range_when_kwarg_absent(self, tmp_path):
        """Databases without the SD kwarg must not grow a stimulus_range column."""
        hardware_info = "{'version': {'id': 'abc'}}"
        db = _make_metadata_db(
            tmp_path,
            hardware_info=hardware_info,
            selected_options=_BASIC_SELECTED_OPTIONS,
        )

        result = load_ethoscope_metadata(_metadata_df(db))

        assert "stimulus_range" not in result.columns

    @pytest.mark.unit
    def test_selected_options_ordered_dict_wrapper(self, tmp_path):
        """Newer firmwares wrap selected_options in OrderedDict(...) — must parse."""
        db = _make_metadata_db(
            tmp_path,
            hardware_info=_REAL_HARDWARE_INFO,
            selected_options=_ORDERED_DICT_SELECTED_OPTIONS,
        )

        result = load_ethoscope_metadata(_metadata_df(db))

        assert len(result) == 1
        assert result.iloc[0]["class"] == "DefaultInteractor"

    @pytest.mark.unit
    def test_missing_file_still_raises(self, tmp_path):
        """A bogus path must still raise — the fix should not mask real errors."""
        metadata = pd.DataFrame(
            {
                "path": [str(tmp_path / "does_not_exist.db")],
                "machine_name": ["ETHOSCOPE_TEST"],
                "date": ["2022-01-01"],
            }
        )
        with pytest.raises(Exception):
            load_ethoscope_metadata(metadata)
