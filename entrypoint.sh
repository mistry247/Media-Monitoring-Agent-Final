#!/bin/sh
# Exit immediately if a command exits with a non-zero status.
set -e

# Run the database initialization script.
echo "--- [Entrypoint] Running database initialization ---"
python init_db.py

# Now, execute the main command (passed to this script).
echo "--- [Entrypoint] Database initialization complete. Starting main application... ---"
exec "$@"
