# Ethoscopy Database Utility Scripts

This directory contains utility scripts for managing and maintaining ethoscope SQLite databases.

## Database Journal Mode Conversion

### convert_wal_to_delete.py

Converts SQLite databases from WAL (Write-Ahead Logging) mode to DELETE mode. This is essential when mounting databases read-only in Docker containers, as WAL mode requires write access to create companion `.db-wal` and `.db-shm` files.

**Usage:**

```bash
# Dry run to preview what would be converted
python3 scripts/convert_wal_to_delete.py /path/to/ethoscope_results --dry-run

# Convert all databases with detailed output
python3 scripts/convert_wal_to_delete.py /path/to/ethoscope_results --verbose

# Force conversion even for recently modified databases (use with caution)
python3 scripts/convert_wal_to_delete.py /path/to/ethoscope_results --force

# Specify custom file pattern
python3 scripts/convert_wal_to_delete.py /path/to/ethoscope_results --pattern "*.sqlite"
```

**Features:**
- Recursively searches for all `.db` files
- Checks current journal mode before conversion
- Safety check: skips files modified within last 24 hours (unless `--force` used)
- Performs WAL checkpoint to merge uncommitted data
- Verifies database integrity after conversion
- Provides detailed progress and summary statistics

### convert_databases.sh

Bash wrapper script that provides a simple interface to the Python conversion script.

**Usage:**

```bash
# Simple one-line conversion
./scripts/convert_databases.sh /path/to/ethoscope_results

# Pass additional flags to the Python script
./scripts/convert_databases.sh /path/to/ethoscope_results --verbose
./scripts/convert_databases.sh /path/to/ethoscope_results --dry-run
```

## When to Use These Scripts

### Problem Symptoms
- Intermittent "database disk image is malformed" errors
- Errors occur when loading ethoscope data in Docker with read-only mounts
- Same ROI sometimes succeeds and sometimes fails to load
- More common with large databases (>1 GB)

### Solution Workflow

1. **Before starting Docker containers:**
   ```bash
   # Convert databases
   ./scripts/convert_databases.sh /mnt/ethoscope_data/results

   # Start containers
   cd Docker && docker compose up -d
   ```

2. **If databases are already mounted:**
   ```bash
   # Convert databases
   ./scripts/convert_databases.sh /mnt/ethoscope_data/results

   # Restart containers to use new connections
   cd Docker && docker compose restart ethoscope-lab
   ```

### Safety Notes

- **Do NOT convert databases while ethoscopes are actively writing to them**
- The script automatically skips files modified within the last 24 hours
- Use `--force` flag to override this safety check if needed
- Always test on a backup or single database first
- Conversion does not modify data, only the internal journal mode

### Verification

Check if a database is in WAL mode:
```bash
sqlite3 database.db "PRAGMA journal_mode;"
```

Verify conversion was successful:
```bash
sqlite3 database.db "PRAGMA journal_mode;"  # Should return: delete
sqlite3 database.db "PRAGMA integrity_check;"  # Should return: ok
```

## Technical Background

**Why this is needed:**

- Ethoscope databases may be created in WAL mode for better write performance
- WAL mode requires companion files (`.db-wal`, `.db-shm`) for proper operation
- Docker read-only mounts (`:ro`) prevent SQLite from accessing these files
- Without proper WAL file access, SQLite can report "database disk image is malformed"
- Converting to DELETE mode eliminates the need for companion files

**What the conversion does:**

1. Executes `PRAGMA wal_checkpoint(TRUNCATE)` - Merges WAL data into main database
2. Executes `PRAGMA journal_mode=DELETE` - Switches to DELETE mode
3. Verifies database integrity with `PRAGMA integrity_check`

The conversion is safe and does not modify any data - it only changes how SQLite manages internal transactions.

## See Also

- `Docker/README.md` - Complete documentation on database preparation for Docker
- `CLAUDE.md` - Troubleshooting section for developer reference
- `src/ethoscopy/load.py` - Implementation of improved connection handling
