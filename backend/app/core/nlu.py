"""Intent, slot extraction and multi-turn context merge.

SRS 5.1 assigns this to an LLM because of genuine natural-language variability
across three languages. No model provider is wired into this build, so what
follows is a deterministic rule layer over the same contract: it returns the
`{intent, slots, language}` shape the graph expects, and swapping in a real
model means replacing `parse_utterance` alone.

The honest limits: it matches keywords, so it will miss phrasings the patterns
do not cover, and it detects Malayalam and Tamil by script without
understanding them. The Coverage tab reports multilingual support as MOCKUP
for exactly this reason.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from backend.app.core import config_store

INTENT_LAYERS = {
    "crossing_safety": ["inlet", "hazard_corridor"],
    "nearest_pfz": ["inlet", "pfz"],
    "geofence_check": ["inlet", "geofences"],
    "route_advisory": ["inlet", "route", "hazard_corridor"],
    "productivity": ["inlet", "anomaly"],
    "coverage": ["inlet", "coverage_line"],
    "greeting": [],
}

_MALAYALAM = re.compile(r"[ഀ-ൿ]")
_TAMIL = re.compile(r"[஀-௿]")

# Malayalam / Tamil keyword stems, so a query in those scripts still routes to
# the right intent even though the response is composed in English.
_ML_SAFE = ("സുരക്ഷ", "പോകാമോ", "കടല", "തിരമാല")
_TA_SAFE = ("பாதுகாப்", "கடல", "அலை", "போகலாம")


def detect_language(text: str) -> str:
    low = text.lower()
    if _MALAYALAM.search(text) or any(w in low.split() for w in ("namaskaram", "sugamano", "engane", "malayalam")):
        return "ml"
    if _TAMIL.search(text) or any(w in low.split() for w in ("vanakkam", "eppadi", "nandri", "tamil", "meen", "kadal")):
        return "ta"
    return "en"


def _detect_intent(low: str, raw: str) -> str:
    if any(w in low.split() for w in ("hi", "hello", "hey", "greetings", "namaste", "vanakkam", "namaskaram", "ഹലോ", "നമസ്കാരം", "வணக்கம்")):
        return "greeting"
    if any(k in raw for k in _ML_SAFE) or any(k in raw for k in _TA_SAFE):
        return "crossing_safety"
    if any(w in low for w in ("pfz", "fishing zone", "fish zone", "where to fish", "shoal")):
        return "nearest_pfz"
    if any(w in low for w in ("zone", "imbl", "protected", "restricted", "boundary", "geofence")):
        return "geofence_check"
    if any(w in low for w in ("route", "corridor", "course", "waypoint", "bearing to")):
        return "route_advisory"
    if any(w in low for w in ("chlorophyll", "productivity", "anomaly", "sst", "bloom")):
        return "productivity"
    if any(w in low for w in ("coverage", "requirement", "matrix")):
        return "coverage"
    return "crossing_safety"


def _detect_date(low: str, base: datetime) -> tuple:
    """Returns (iso_date, label) or (None, None) when the utterance says nothing."""
    if "day after" in low:
        d = base + timedelta(days=2)
        return d.date().isoformat(), "Day after tomorrow"
    if "tomorrow" in low or "നാളെ" in low or "நாளை" in low:
        d = base + timedelta(days=1)
        return d.date().isoformat(), "Tomorrow"
    if "today" in low or "tonight" in low or "ഇന്ന" in low or "இன்று" in low:
        return base.date().isoformat(), "Today"
    if "next week" in low:
        d = base + timedelta(days=7)
        return d.date().isoformat(), "Next week"
    m = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", low)
    if m:
        return m.group(1), m.group(1)
    return None, None


def _detect_hull(low: str) -> str:
    """Match an utterance to a hull class in D-10, by keyword or by length."""
    if "canoe" in low or "vallam" in low or "plywood" in low:
        return "PLYWOOD_CANOE"
    if "deep" in low and "trawler" in low:
        return "TRAWLER_DEEP"
    if "trawler" in low or "mechanised" in low or "mechanized" in low:
        return "TRAWLER_MED"
    if "frp" in low or "skiff" in low or "fibre" in low or "fiber" in low:
        return "FRP_SMALL"

    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:m|metre|meter)\b", low)
    if m:
        length = float(m.group(1))
        if length < 7.0:
            return "PLYWOOD_CANOE"
        if length < 11.0:
            return "FRP_SMALL"
        if length < 18.0:
            return "TRAWLER_MED"
        return "TRAWLER_DEEP"
    return ""


def _detect_time_of_day(low: str) -> tuple:
    if "morning" in low:
        return 6, 12
    if "afternoon" in low:
        return 12, 18
    if "evening" in low or "night" in low:
        return 16, 22
    return 0, 0


def parse_utterance(text: str, context: Dict[str, Any],
                    now: datetime = None) -> Dict[str, Any]:
    """Merge a new utterance into retained context.

    FR-03: only fields the utterance actually states are overwritten. Anything
    it is silent about keeps its previous value, which is what makes
    "And the day after?" work as a third turn.
    """
    base = now or datetime.now(timezone.utc)
    raw = text or ""
    low = raw.lower()

    slots: Dict[str, Any] = {
        "location": context.get("location") or "Muthalapozhi",
        "date": context.get("date") or base.date().isoformat(),
        "time_label": context.get("time_label") or "Today",
        "hull_class": context.get("hull_class") or "",
        "ground_id": context.get("ground_id") or "",
        "departure_hour": context.get("departure_hour") or 6,
        "return_hour": context.get("return_hour") or 18,
    }
    updated: List[str] = []

    date_iso, date_label = _detect_date(low, base)
    if date_iso:
        slots["date"] = date_iso
        slots["time_label"] = date_label
        updated.append("time_window")

    hull = _detect_hull(low)
    if hull:
        slots["hull_class"] = hull
        updated.append("boat")

    dep, ret = _detect_time_of_day(low)
    if dep or ret:
        slots["departure_hour"] = dep
        slots["return_hour"] = ret
        if "time_window" not in updated:
            updated.append("time_window")

    for ground in _known_grounds():
        if ground.lower() in low:
            slots["ground_id"] = ground
            updated.append("location")
            break

    intent = _detect_intent(low, raw)

    return {
        "intent": intent,
        "slots": slots,
        "language": detect_language(raw),
        "updated_fields": updated,
        "layers": INTENT_LAYERS.get(intent, INTENT_LAYERS["crossing_safety"]),
    }


def _known_grounds() -> List[str]:
    from backend.app.core.seed_data import NAMED_GROUNDS
    return [g["local_name"] for g in NAMED_GROUNDS]


def hull_label(hull_class: str) -> str:
    return config_store.hull_threshold(hull_class).get("label", hull_class)
