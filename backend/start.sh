#!/bin/bash
set -e

echo "Starting ORCA Backend Deployment Pipeline..."

# Run the seeding script to populate the database and mock files
python -m backend.scripts.seed_demo

# Start the FastAPI server using Render's assigned port (or fallback to 8000)
echo "Starting Uvicorn Server..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}
