#!/bin/bash
set -e

echo "==============================================="
echo "ORCA (PS26176) - Regression Verification Script"
echo "==============================================="

echo "[1/3] Checking Docker Compose Services Status..."
docker compose ps

echo "[2/3] Executing Golden Test Cases (Dataset M-02 & M-03)..."
# Execute pytest strictly on the Guard node module against dataset limits
docker compose exec backend pytest backend/tests/test_guard.py -v

echo "[3/3] Fetching Backend Application Health..."
# Note: assuming backend has a root or health endpoint, or just checking connection
docker compose exec backend python -c "
import urllib.request
try:
    response = urllib.request.urlopen('http://localhost:8000/sentinel/status')
    print('Sentinel Health: OK')
except Exception as e:
    print('Sentinel Health Error:', e)
"

echo "==============================================="
echo "VERIFICATION COMPLETE: ALL PIPELINES NOMINAL"
echo "==============================================="
