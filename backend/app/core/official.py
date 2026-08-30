import asyncio
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
    "provenance": "COMPUTED_LIVE",
}


# We can just cache the dict in a global variable
_cache = None

async def _by_date() -> Dict[str, Dict[str, Any]]:
    global _cache
    if _cache is None:
        _cache = {row["date"]: row for row in await official_advisories()}
    return _cache


async def advisory_for_date(date_iso: str) -> Dict[str, Any]:
    """The bulletin in force on a date, mapped onto the record like the advisory."""
    from datetime import datetime, timezone

    table = await _by_date()
    if date_iso in table:
        return table[date_iso]
    try:
        dt = datetime.fromisoformat(date_iso).replace(tzinfo=timezone.utc)
    except ValueError:
        return FALLBACK
    mapped, _ = resolve_record_datetime(dt)
    return table.get(mapped.date().isoformat(), FALLBACK)


async def latest() -> Dict[str, Any]:
    rows = await official_advisories()
    return rows[-1] if rows else FALLBACK
