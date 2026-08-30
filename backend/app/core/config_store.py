"""Loader for the file-backed static config (D-10, D-12, D-13, D-14, D-16).

These live as JSON rather than Python so a persona, a coverage row, a hull
threshold or a data source can be edited without touching agent code
(FR-08, FR-28) and without a redeploy.
"""
import json
import os
from functools import lru_cache
from typing import Any, Dict, List

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")


def _load(name: str) -> Dict[str, Any]:
    with open(os.path.join(CONFIG_DIR, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=None)
def _cached(name: str) -> Dict[str, Any]:
    return _load(name)


def reload_all() -> None:
    """Drop the cache so an edited config file is picked up in place."""
    _cached.cache_clear()


def hull_thresholds() -> List[Dict[str, Any]]:
    from backend.app.db.supabase import supabase
    if supabase:
        try:
            res = supabase.table("vessels").select("*").execute()
            if res.data:
                # Map standard DB column names to what ThresholdBand expects if necessary
                return res.data
        except Exception as e:
            print(f"Supabase vessels error: {e}")
    # Fallback to local JSON if no DB
    return _cached("hull_thresholds.json")["rows"]


def hull_threshold(hull_class: str) -> Dict[str, Any]:
    rows = hull_thresholds()
    for row in rows:
        if row.get("hull_class") == hull_class:
            return row
    return min(rows, key=lambda r: r.get("index_unsafe", 1.0))


def personas() -> List[Dict[str, Any]]:
    return _cached("personas.json")["rows"]


def persona(persona_id: str) -> Dict[str, Any]:
    for row in personas():
        if row["persona_id"] == persona_id:
            return row
    return personas()[0]


def coverage_rows() -> List[Dict[str, Any]]:
    return _cached("coverage.json")["rows"]


def channels() -> Dict[str, Any]:
    return _cached("channels.json")


def registry_seed() -> List[Dict[str, Any]]:
    return _cached("source_registry.json")["rows"]


class ThresholdBand:
    """Adapter giving hazard_engine.evaluate_verdict the attributes it expects."""

    def __init__(self, row: Dict[str, Any]):
        self.hull_class = row["hull_class"]
        self.label = row.get("label", row["hull_class"])
        self.index_marginal = row["index_marginal"]
        self.index_unsafe = row["index_unsafe"]
        self.hs_marginal_m = row.get("hs_marginal_m")
        self.hs_unsafe_m = row.get("hs_unsafe_m")
        self.cruise_knots = row.get("cruise_knots", 7.0)


def band_for(hull_class: str) -> ThresholdBand:
    return ThresholdBand(hull_threshold(hull_class))
