#!/bin/bash
set -e

# Schema creation and seeding happen in the FastAPI lifespan (see
# backend/app/db/bootstrap.py), so there is no separate seed step to forget.
# With no DATABASE_URL set the app falls back to a local SQLite file.
echo "Starting ORCA API on port ${PORT:-8000}..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
