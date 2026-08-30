"""Turns a boat and a time window into a complete, auditable advisory.

Every number this module emits comes from the deterministic engine in
`hazard_engine`. Explanation text is assembled by template substitution from
that same payload, never generated free-form, so R-7 (number injection) holds
by construction and the guard has something real to check.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend.app.core import config_store
from backend.app.core.dataset import (
    INLET,
    RECORD_START,
    RECORD_YEARS,
    row_at,
    tide_data,
    wave_data,
    window as record_window,
)
from backend.app.core.hazard_engine import calculate_hazard_index, evaluate_verdict

# Default crossing plan when the query does not state one.
DEFAULT_DEPARTURE_HOUR = 6
DEFAULT_RETURN_HOUR = 18
DEFAULT_GROUND_DISTANCE_NM = 12.0

RECORD_END = RECORD_START + timedelta(days=RECORD_YEARS * 365 - 1)

VERDICT_ORDER = {"SAFE": 0, "MARGINAL": 1, "DO_NOT_CROSS": 2}


def resolve_record_datetime(dt: datetime) -> Tuple[datetime, bool]:
    """Ensure the target datetime is UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt, False


async def hourly_forecast(start: datetime, end: datetime, lat: float = INLET["lat"], lon: float = INLET["lon"]) -> List[Dict[str, Any]]:
    """Analysis rows shaped for `compute_return_window_and_turnback`."""
    rows = await record_window(start, end, lat, lon)
    return [
        {
            "timestamp": row["ts"],
            "wave_data": wave_data(row),
            "tide_data": tide_data(row),
            "inlet_geometry": {"channel_bearing": INLET["channel_bearing_deg"]},
            "lightning_flag": row["lightning_flag"],
            "cyclone_flag": row["cyclone_flag"],
        }
        for row in rows
    ]


def _index_for(row: Dict[str, Any]) -> float:
    return calculate_hazard_index(
        wave_data(row),
        tide_data(row),
        {"channel_bearing": INLET["channel_bearing_deg"]},
        row["lightning_flag"],
        row["cyclone_flag"],
    )


async def build_advisory(
    hull_class: str,
    target: datetime,
    departure_hour: int = DEFAULT_DEPARTURE_HOUR,
    return_hour: int = DEFAULT_RETURN_HOUR,
    distance_nm: float = DEFAULT_GROUND_DISTANCE_NM,
    lat: float = INLET["lat"],
    lon: float = INLET["lon"],
) -> Dict[str, Any]:
    """Compute the full advisory payload for one hull on one day."""
    band = config_store.band_for(hull_class)
    mapped, was_mapped = resolve_record_datetime(target)

    departure = mapped.replace(hour=departure_hour, minute=0, second=0, microsecond=0)
    deadline = mapped.replace(hour=return_hour, minute=0, second=0, microsecond=0)
    if deadline <= departure:
        deadline = departure + timedelta(hours=8)

    rows = await record_window(departure, deadline, lat, lon)
    if not rows:
        rows = [await row_at(departure, lat, lon)]

    hourly = []
    for row in rows:
        idx = _index_for(row)
        hourly.append({
            "ts": row["ts"].isoformat(),
            "hour": row["ts"].hour,
            "index": round(idx, 3),
            "verdict": evaluate_verdict(idx, band),
            "hs_m": row["hs_m"],
            "tp_s": row["tp_s"],
            "dir_deg": row["dir_deg"],
            "swell_hs_m": row["swell_hs_m"],
            "tide_stage": row["tide_stage"],
            "lightning_flag": row["lightning_flag"],
            "cyclone_flag": row["cyclone_flag"],
        })

    # The advisory takes the worst hour in the window: a bar that is
    # impassable at 14:00 is not a safe day because 06:00 was calm.
    peak = max(hourly, key=lambda h: h["index"])
    peak_row = rows[hourly.index(peak)]
    index_value = peak["index"]
    verdict = peak["verdict"]

    from backend.app.core.hazard_engine import compute_return_window_and_turnback

    window, turn_back = compute_return_window_and_turnback(
        await hourly_forecast(departure, deadline, lat, lon),
        departure,
        deadline,
        boat_speed_knots=band.cruise_knots,
        distance_nm=distance_nm,
        hull_threshold=band,
    )

    is_custom = abs(lat - INLET["lat"]) > 0.05 or abs(lon - INLET["lon"]) > 0.05
    loc_name = "Coastal Waters (GPS)" if is_custom else INLET["name"]
    loc_id = "gps" if is_custom else INLET["inlet_id"]

    payload: Dict[str, Any] = {
        "inlet_id": loc_id,
        "inlet_name": loc_name,
        "hull_class": band.hull_class,
        "hull_label": band.label,
        "date": mapped.date().isoformat(),
        "verdict": verdict,
        "index_value": index_value,
        "index_marginal": band.index_marginal,
        "index_unsafe": band.index_unsafe,
        "hs_m": peak_row["hs_m"],
        "tp_s": peak_row["tp_s"],
        "dir_deg": peak_row["dir_deg"],
        "swell_hs_m": peak_row["swell_hs_m"],
        "wind_ms": peak_row["wind_ms"],
        "tide_stage": peak_row["tide_stage"],
        "channel_bearing_deg": INLET["channel_bearing_deg"] if not is_custom else 270.0,
        "lightning_flag": peak_row["lightning_flag"],
        "cyclone_flag": peak_row["cyclone_flag"],
        "peak_hour": peak["hour"],
        "cruise_knots": band.cruise_knots,
        "distance_nm": distance_nm,
        "hourly": hourly,
        "date_mapped_from_request": was_mapped,
        "staleness_hours": 0.0,
        "provenance": "SYNTHETIC_STRUCTURED",
    }

    if window:
        payload["return_window"] = {
            "start": window[0].isoformat(),
            "end": window[1].isoformat(),
            "start_label": window[0].strftime("%H:%M"),
            "end_label": window[1].strftime("%H:%M"),
        }
    else:
        payload["return_window"] = None

    payload["turn_back_time"] = turn_back.isoformat() if turn_back else None
    payload["turn_back_label"] = turn_back.strftime("%H:%M") if turn_back else None

    payload["explanation"] = _explain(payload)
    payload["_numerals"] = _numerals(payload)
    return payload


def _explain(p: Dict[str, Any]) -> str:
    """Templated explanation. Every numeral is substituted from `p`."""
    inlet = p["inlet_name"]
    hull = p["hull_label"]

    if p["cyclone_flag"]:
        driver = "an active cyclone warning covers this stretch of coast"
    elif p["lightning_flag"]:
        driver = "lightning was detected within the harbour alert radius"
    elif p["tide_stage"] == "ebb":
        driver = (f"a {p['hs_m']} m swell at {p['tp_s']} s meets an outgoing ebb "
                  f"tide across the bar")
    else:
        driver = f"the swell runs at {p['hs_m']} m with a {p['tp_s']} s period"

    head = {
        "SAFE": f"Crossing {inlet} is within limits for a {hull}.",
        "MARGINAL": f"Crossing {inlet} is marginal for a {hull}.",
        "DO_NOT_CROSS": f"Do not cross {inlet} in a {hull}.",
    }[p["verdict"]]

    body = (f"The hazard index peaks at {p['index_value']} around "
            f"{p['peak_hour']}:00, against a limit of {p['index_unsafe']} for this hull, "
            f"because {driver}.")

    if p["return_window"] and p["turn_back_label"]:
        tail = (f"The bar stays passable from {p['return_window']['start_label']} to "
                f"{p['return_window']['end_label']}; turn back by "
                f"{p['turn_back_label']} to be inside that window at "
                f"{p['cruise_knots']} knots.")
    elif p["return_window"]:
        tail = (f"The bar is passable from {p['return_window']['start_label']} to "
                f"{p['return_window']['end_label']}, but there is no departure time "
                f"that gets a {hull} back inside it.")
    else:
        tail = "There is no passable return window for this hull today."

    return f"{head} {body} {tail}"


def _numerals(p: Dict[str, Any]) -> List[float]:
    """Every number the template is permitted to inject.

    The guard checks generated text against the computed payload; clock times
    decompose into their hour and minute components, so those are listed here
    explicitly rather than left for the guard to fail on.
    """
    nums: List[float] = []
    for key in ("index_value", "index_unsafe", "index_marginal", "hs_m", "tp_s",
                "swell_hs_m", "wind_ms", "dir_deg", "peak_hour", "cruise_knots",
                "distance_nm", "channel_bearing_deg"):
        if isinstance(p.get(key), (int, float)):
            nums.append(float(p[key]))
    nums.append(0.0)  # the ":00" of the peak hour

    for label_key in ("turn_back_label",):
        label = p.get(label_key)
        if label:
            hh, mm = label.split(":")
            nums.extend([float(hh), float(mm), float(hh.lstrip("0") or 0)])

    rw = p.get("return_window")
    if rw:
        for label in (rw["start_label"], rw["end_label"]):
            hh, mm = label.split(":")
            nums.extend([float(hh), float(mm), float(hh.lstrip("0") or 0)])

    return sorted({round(n, 4) for n in nums})


async def compare_hulls(target: datetime, hull_classes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Same conditions, every hull class - the FR-13 differentiation view."""
    classes = hull_classes or [r["hull_class"] for r in config_store.hull_thresholds()]
    out = []
    for hc in classes:
        a = await build_advisory(hc, target)
        out.append({
            "hull_class": a["hull_class"],
            "hull_label": a["hull_label"],
            "verdict": a["verdict"],
            "index_value": a["index_value"],
            "index_marginal": a["index_marginal"],
            "index_unsafe": a["index_unsafe"],
            "turn_back_label": a["turn_back_label"],
        })
    return out
