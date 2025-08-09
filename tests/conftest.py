"""
Pytest configuration and shared fixtures for ethoscopy tests.
"""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import ethoscopy as etho


@pytest.fixture
def real_ethoscope_db():
    """
    Fixture providing path to real ethoscope database file for testing.

    Returns:
        Path: Path to the real test database file
    """
    test_db_path = Path(__file__).parent / "data" / "test_ethoscope.db"
    if not test_db_path.exists():
        pytest.skip("Real test database file not found. Run: make test-data")
    return test_db_path


@pytest.fixture
def sample_metadata_csv(tmp_path):
    """
    Create a sample metadata CSV file for testing.

    Returns:
        Path: Path to the temporary CSV file
    """
    metadata_data = {
        "date": ["2025-01-01", "2025-01-01", "2025-01-01"],
        "machine_name": ["ETHOSCOPE_001", "ETHOSCOPE_001", "ETHOSCOPE_002"],
        "region_id": [1, 2, 1],
        "sex": ["male", "female", "male"],
        "species": ["test_species", "test_species", "test_species"],
        "food": ["normal", "normal", "normal"],
        "baseline": [0, 0, 0],
        "sleep_deprived": [False, True, False],
        "incubator": [25.0, 25.0, 25.0],
    }

    df = pd.DataFrame(metadata_data)
    csv_path = tmp_path / "test_metadata.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def sample_ethoscope_data():
    """
    Create sample ethoscope tracking data.

    Returns:
        pd.DataFrame: Sample tracking data
    """
    np.random.seed(42)  # For reproducible tests
    n_points = 7200  # Increase density to ~2 points/second for 1 hour

    data = pd.DataFrame(
        {
            "id": [1] * n_points,
            "t": np.linspace(0, 3600, n_points),  # 1 hour of data
            "x": np.random.normal(100, 10, n_points),
            "y": np.random.normal(100, 10, n_points),
            "w": np.random.normal(10, 1, n_points),
            "h": np.random.normal(10, 1, n_points),
            "phi": np.random.uniform(0, 2 * np.pi, n_points),
            "xy_dist_log10x1000": np.random.exponential(100, n_points),
            "is_inferred": np.random.choice([0, 1], n_points, p=[0.9, 0.1]),
            "has_interacted": np.random.choice([0, 1], n_points, p=[0.95, 0.05]),
        }
    )

    return data


@pytest.fixture
def mock_sqlite_db(tmp_path, sample_ethoscope_data):
    """
    Create a mock SQLite database file with ethoscope structure.

    Args:
        tmp_path: Pytest temporary directory fixture
        sample_ethoscope_data: Sample tracking data fixture

    Returns:
        Path: Path to the mock database file
    """
    db_path = tmp_path / "test_ethoscope.db"

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create ROI_MAP table
    cursor.execute(
        """
        CREATE TABLE ROI_MAP (
            roi_idx INTEGER PRIMARY KEY,
            x INTEGER,
            y INTEGER,
            w INTEGER,
            h INTEGER
        )
    """
    )

    # Insert sample ROI data
    cursor.execute("INSERT INTO ROI_MAP VALUES (1, 50, 50, 100, 100)")
    cursor.execute("INSERT INTO ROI_MAP VALUES (2, 200, 50, 100, 100)")

    # Create VAR_MAP table
    cursor.execute(
        """
        CREATE TABLE VAR_MAP (
            var_name TEXT,
            functional_type TEXT,
            sql_data_type TEXT
        )
    """
    )

    # Insert variable mappings
    vars_data = [
        ("x", "position", "REAL"),
        ("y", "position", "REAL"),
        ("w", "size", "REAL"),
        ("h", "size", "REAL"),
        ("phi", "angle", "REAL"),
        ("xy_dist_log10x1000", "distance", "REAL"),
    ]

    cursor.executemany("INSERT INTO VAR_MAP VALUES (?, ?, ?)", vars_data)

    # Create METADATA table
    cursor.execute(
        """
        CREATE TABLE METADATA (
            field TEXT,
            value TEXT
        )
    """
    )

    # Insert metadata
    cursor.execute(
        'INSERT INTO METADATA VALUES ("date_time", "1640995200")'
    )  # 2022-01-01 00:00:00 UTC
    cursor.execute(
        "INSERT INTO METADATA VALUES (\"experimental_info\", \"{'test': 'data', 'partitions': [1, 2]}\")"
    )  # Sample experimental info
    cursor.execute(
        "INSERT INTO METADATA VALUES (\"hardware_info\", \"{'version': {'ethoscope_version': '1.0'}, 'partitions': [1, 2]}\")"
    )  # Sample hardware info
    cursor.execute(
        "INSERT INTO METADATA VALUES (\"selected_options\", \"{'option1': 'value1'}\")"
    )  # Sample selected options

    # Create ROI_1 table with sample data
    sample_ethoscope_data.to_sql("ROI_1", conn, if_exists="replace", index=False)

    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def sample_behavpy_object(sample_ethoscope_data):
    """
    Create a sample behavpy object for testing.

    Args:
        sample_ethoscope_data: Sample tracking data fixture

    Returns:
        behavpy: Sample behavpy object
    """
    metadata = pd.DataFrame(
        {
            "id": ["test_id_01"],
            "sex": ["male"],
            "species": ["test_species"],
            "date": ["2025-01-01"],
        }
    )

    return etho.behavpy(sample_ethoscope_data, metadata, check=False)


@pytest.fixture
def linked_metadata_sample(tmp_path, mock_sqlite_db):
    """
    Create sample linked metadata for testing load functions.

    Args:
        tmp_path: Pytest temporary directory fixture
        mock_sqlite_db: Mock database fixture

    Returns:
        pd.DataFrame: Linked metadata dataframe
    """
    # Create directory structure that matches ethoscope organization
    machine_dir = tmp_path / "test_machine" / "ETHOSCOPE_001" / "2025-01-01_12-00-00"
    machine_dir.mkdir(parents=True)

    # Copy the mock database to the expected location
    db_dest = machine_dir / "test_ethoscope.db"
    import shutil

    shutil.copy2(mock_sqlite_db, db_dest)

    # Create linked metadata
    linked_metadata = pd.DataFrame(
        {
            "id": ["2025-01-01_12-00-00_test|01"],
            "date": ["2025-01-01"],
            "machine_name": ["ETHOSCOPE_001"],
            "region_id": [1],
            "sex": ["male"],
            "species": ["test_species"],
            "food": ["normal"],
            "baseline": [0],
            "sleep_deprived": [False],
            "incubator": [25.0],
            "machine_id": ["test_machine_id"],
            "file_name": ["test_ethoscope.db"],
            "path": [str(db_dest)],
            "file_size": [db_dest.stat().st_size],
            "time": ["12-00-00"],
        }
    )

    return linked_metadata
