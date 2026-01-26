#!/usr/bin/env python3
"""
Convert SQLite databases from WAL mode to DELETE mode for read-only Docker mounts.

This script walks through a directory tree, finds all SQLite database files,
and converts them from WAL (Write-Ahead Logging) mode to DELETE mode.
This is necessary for ethoscope databases that will be mounted read-only in Docker.

Usage:
    python convert_wal_to_delete.py /path/to/ethoscope_results
    python convert_wal_to_delete.py /path/to/ethoscope_results --dry-run
    python convert_wal_to_delete.py /path/to/ethoscope_results --verbose
    python convert_wal_to_delete.py /path/to/ethoscope_results --force
"""

import argparse
import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Tuple, List


def check_journal_mode(db_path: Path) -> str:
    """Check the current journal mode of a SQLite database."""
    try:
        conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0]
        conn.close()
        return mode
    except Exception as e:
        return f"ERROR: {str(e)}"


def convert_database(db_path: Path, force: bool = False, verbose: bool = False) -> Tuple[bool, str]:
    """
    Convert a database from WAL to DELETE mode.

    Args:
        db_path: Path to the database file
        force: If True, skip safety checks for recently modified files
        verbose: If True, print detailed progress

    Returns:
        Tuple of (success, message)
    """
    try:
        # Check if file was recently modified (within last 24 hours)
        if not force:
            mtime = datetime.fromtimestamp(db_path.stat().st_mtime)
            if datetime.now() - mtime < timedelta(hours=24):
                return False, "SKIPPED: Database modified within last 24 hours (use --force to override)"

        # Check current journal mode
        current_mode = check_journal_mode(db_path)
        if "ERROR" in current_mode:
            return False, f"FAILED: Could not read journal mode: {current_mode}"

        if current_mode.lower() == 'delete':
            return True, "SKIPPED: Already in DELETE mode"

        if verbose:
            print(f"  Current mode: {current_mode}")

        # Open database in read-write mode for conversion
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Checkpoint the WAL file to merge changes back to main database
        if verbose:
            print(f"  Checkpointing WAL...")
        cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);")

        # Convert to DELETE mode
        if verbose:
            print(f"  Converting to DELETE mode...")
        cursor.execute("PRAGMA journal_mode=DELETE;")
        new_mode = cursor.fetchone()[0]

        # Verify integrity
        if verbose:
            print(f"  Verifying integrity...")
        cursor.execute("PRAGMA integrity_check;")
        integrity = cursor.fetchone()[0]

        conn.close()

        if integrity.lower() != 'ok':
            return False, f"FAILED: Integrity check failed: {integrity}"

        if new_mode.lower() != 'delete':
            return False, f"FAILED: Conversion unsuccessful, mode is {new_mode}"

        return True, f"SUCCESS: Converted from {current_mode} to {new_mode}"

    except sqlite3.OperationalError as e:
        return False, f"FAILED: Database locked or in use: {str(e)}"
    except Exception as e:
        return False, f"FAILED: {str(e)}"


def find_databases(root_path: Path, pattern: str = "*.db") -> List[Path]:
    """Find all database files in the directory tree."""
    return list(root_path.rglob(pattern))


def main():
    parser = argparse.ArgumentParser(
        description="Convert SQLite databases from WAL mode to DELETE mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to see what would be converted
  python convert_wal_to_delete.py /mnt/ethoscope_data/results --dry-run

  # Convert all databases with verbose output
  python convert_wal_to_delete.py /mnt/ethoscope_data/results --verbose

  # Force conversion even for recently modified databases
  python convert_wal_to_delete.py /mnt/ethoscope_data/results --force
        """
    )

    parser.add_argument(
        'root_path',
        type=Path,
        help='Root directory to search for database files'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed progress information'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force conversion even for recently modified databases'
    )
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.db',
        help='File pattern to match (default: *.db)'
    )

    args = parser.parse_args()

    # Validate root path
    if not args.root_path.exists():
        print(f"ERROR: Path does not exist: {args.root_path}", file=sys.stderr)
        sys.exit(1)

    if not args.root_path.is_dir():
        print(f"ERROR: Path is not a directory: {args.root_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Searching for database files in: {args.root_path}")
    print(f"Pattern: {args.pattern}")

    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")

    print()

    # Find all database files
    databases = find_databases(args.root_path, args.pattern)

    if not databases:
        print("No database files found.")
        sys.exit(0)

    print(f"Found {len(databases)} database file(s)")
    print()

    # Process each database
    stats = {
        'total': len(databases),
        'converted': 0,
        'skipped': 0,
        'failed': 0,
        'already_delete': 0
    }

    for i, db_path in enumerate(databases, 1):
        rel_path = db_path.relative_to(args.root_path)
        size_mb = db_path.stat().st_size / (1024 * 1024)

        print(f"[{i}/{len(databases)}] {rel_path} ({size_mb:.1f} MB)")

        if args.dry_run:
            mode = check_journal_mode(db_path)
            print(f"  Current mode: {mode}")
            if mode.lower() == 'wal':
                print(f"  Would convert from WAL to DELETE")
            elif mode.lower() == 'delete':
                print(f"  Already in DELETE mode")
            stats['skipped'] += 1
        else:
            success, message = convert_database(db_path, args.force, args.verbose)
            print(f"  {message}")

            if success:
                if "Already in DELETE mode" in message:
                    stats['already_delete'] += 1
                else:
                    stats['converted'] += 1
            elif "SKIPPED" in message:
                stats['skipped'] += 1
            else:
                stats['failed'] += 1

        print()

    # Print summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total databases found:     {stats['total']}")

    if args.dry_run:
        print(f"Would be processed:        {stats['skipped']}")
    else:
        print(f"Successfully converted:    {stats['converted']}")
        print(f"Already in DELETE mode:    {stats['already_delete']}")
        print(f"Skipped:                   {stats['skipped']}")
        print(f"Failed:                    {stats['failed']}")

    if stats['failed'] > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
