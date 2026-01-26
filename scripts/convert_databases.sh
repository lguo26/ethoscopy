#!/bin/bash
# Wrapper script to convert all ethoscope databases from WAL to DELETE mode
# Run this BEFORE docker compose up to prepare databases for read-only mounting
#
# Usage:
#   ./convert_databases.sh /mnt/ethoscope_data/results
#   ./convert_databases.sh /mnt/ethoscope_data/results --dry-run

set -e

# Default path if not provided
DATA_PATH="${1:-/mnt/ethoscope_data/results}"

# Check if path exists
if [ ! -d "$DATA_PATH" ]; then
    echo "ERROR: Directory does not exist: $DATA_PATH"
    echo "Usage: $0 <path_to_ethoscope_results> [--dry-run]"
    exit 1
fi

echo "Converting SQLite databases in: $DATA_PATH"
echo "This may take a while for large datasets..."
echo ""

# Check if Python script exists
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/convert_wal_to_delete.py"

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "ERROR: Python script not found: $PYTHON_SCRIPT"
    exit 1
fi

# Pass all arguments to the Python script
python3 "$PYTHON_SCRIPT" "$@"

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✓ Database conversion completed successfully"
    echo ""
    echo "You can now start Docker containers with:"
    echo "  cd $(dirname "$SCRIPT_DIR") && docker compose up -d"
else
    echo ""
    echo "✗ Database conversion failed with exit code $exit_code"
    echo "Please check the errors above and try again"
fi

exit $exit_code
