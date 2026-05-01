#!/bin/bash
set -e

echo "=== CodeRubric Backend Entrypoint ==="

# Ensure persistent directories exist
mkdir -p /app/data/repos

# Run database table creation (SQLAlchemy create_all is idempotent)
echo "Running database migrations..."
python -c "from backend.database import init_db; init_db()"
echo "Database ready."

# Start the application
echo "Starting uvicorn..."
exec uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
