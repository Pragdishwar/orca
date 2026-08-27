#!/bin/bash
# End-to-end check that the prototype actually does what the Coverage tab claims.
# Usage: ./verify_build.sh [base_url]      default http://127.0.0.1:8000
set -e
BASE="${1:-http://127.0.0.1:8000}"
SID=$(python -c "import uuid;print(uuid.uuid4())")

say() { printf '\n\033[1m== %s\033[0m\n' "$1"; }
q()   { curl -sS -X POST "$BASE/api/query" -H 'Content-Type: application/json' \
          -d "{\"session_id\":\"$SID\",\"query_text\":\"$1\",\"force_failure\":${2:-false}}"; }

say "Unit tests"
python -m pytest -q

say "Health"
curl -sS "$BASE/api/health"

say "Turn 1 — crossing verdict, discovery, hinge"
q "Is it safe to go out tomorrow morning?" | python -m json.tool | head -30

say "Turn 2 — context carries, only the date changes"
q "And the day after?" | python -c "import sys,json;d=json.load(sys.stdin);print('date',d['date'],'hull',d['hull_class'],'updated',d['updated_fields'])"

say "Turn 3 — hull changes, date is retained, verdict changes"
q "What about the 12 m trawler?" | python -c "import sys,json;d=json.load(sys.stdin);print('date',d['date'],'hull',d['hull_class'],'verdict',d['verdict'],'updated',d['updated_fields'])"

say "Guard rejects a forced contradiction"
q "Is it safe tomorrow?" true | python -c "import sys,json;d=json.load(sys.stdin);print('guard',d['guard'])"

say "Validation recomputes at three operating points"
for t in 0.35 0.44 0.55; do
  curl -sS "$BASE/api/validation?threshold=$t" | python -c "import sys,json;d=json.load(sys.stdin);c=d['contingency'];print(' thr',d['threshold'],'POD',c['pod'],'FAR',c['far'],'days/yr',c['days_per_year'])"
done

say "Sentinel poll produces alerts with no query asked"
curl -sS -X POST "$BASE/api/sentinel/trigger" | python -m json.tool

say "Coverage matrix"
curl -sS "$BASE/api/coverage" | python -c "import sys,json;d=json.load(sys.stdin);print(d['summary'])"

printf '\n\033[1;32mAll checks completed.\033[0m\n'
