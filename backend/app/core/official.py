"""Lookup for the official advisory strip (D-11, FR-19)."""
from functools import lru_cache
from typing import Any, Dict

from backend.app.core.advisory_engine import resolve_record_datetime
from backend.app.core.seed_data import official_advisories

FALLBACK = {
    "date": None,
    "issuer": "INCOIS",
    "region": "Kerala coast",
    "text_en": "No official advisory is on file for this date.",
    "text_ml": "",
    "severity": "advisory",
    "provenance": "SYNTHETIC_STRUCTURED",
}


@lru_cache(maxsize=1)
def _by_date() -> Dict[str, Dict[str, Any]]:
    return {row["date"]: row for row in official_advisories()}


def advisory_for_date(date_iso: str) -> Dict[str, Any]:
    """The bulletin in force on a date, mapped onto the record like the advisory."""
    from datetime import datetime, timezone

    table = _by_date()
    if date_iso in table:
        return table[date_iso]
    try:
        dt = datetime.fromisoformat(date_iso).replace(tzinfo=timezone.utc)
    except ValueError:
        return FALLBACK
    mapped, _ = resolve_record_datetime(dt)
    return table.get(mapped.date().isoformat(), FALLBACK)


def latest() -> Dict[str, Any]:
    rows = official_advisories()
    return rows[-1] if rows else FALLBACK
